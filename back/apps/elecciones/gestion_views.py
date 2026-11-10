"""Gestión de Ediciones y Categorías por el sitio MVT (ED1-ED4, CA1-CA3).

Toda la gestión exige permisos del catálogo vía ``@requiere_permiso``; el
bloqueo de borrados y las transiciones de estado se validan aquí.
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from back.apps.auditoria.servicio import registrar_evento
from back.apps.usuarios.permisos import requiere_permiso, tiene_permiso

from .gestion_forms import (
    CategoriaForm,
    EdicionCategoriaForm,
    EdicionForm,
    OpcionForm,
    VotacionForm,
)
from .models import Categoria, Edicion, Opcion, Votacion


def _siguiente(request):
    """URL interna a la que volver tras una acción (``?siguiente=``).

    Permite que la pantalla de una edición recupere el control después de
    crear, editar, abrir o cerrar una votación. Solo acepta rutas de este
    mismo sitio, para no abrir una redirección a otro dominio.
    """
    destino = request.POST.get('siguiente') or request.GET.get('siguiente') or ''
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return ''


def _volver(request, por_defecto, *args):
    """Redirige a ``siguiente`` si es válido; si no, a la ruta por defecto."""
    return redirect(_siguiente(request) or por_defecto, *args)


# --------------------------------------------------------------------------
# Ediciones (ED1, ED2, ED3, ED4)
# --------------------------------------------------------------------------

@requiere_permiso('ediciones.ver')
def edicion_lista(request):
    """ED1: nombre, año, estado y cantidad de votaciones."""
    return render(
        request,
        'gestion/edicion_lista.html',
        {
            'ediciones': (
                Edicion.objects.annotate(num_votaciones=Count('votaciones'))
                .order_by('-anio', 'nombre')
            ),
            'puede_crear': tiene_permiso(request.user, 'ediciones.crear'),
        },
    )


@requiere_permiso('ediciones.crear')
def edicion_crear(request):
    """ED2: alta de una edición."""
    form = EdicionForm(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        edicion = form.save()
        registrar_evento(request, 'ediciones', 'edicion_creada', {'id': edicion.id})
        messages.success(request, f'Edición «{edicion}» creada.')
        return redirect('gestion:ediciones')

    return render(request, 'gestion/edicion_form.html', {'form': form, 'titulo': 'Nueva edición'})


@requiere_permiso('ediciones.editar')
def edicion_editar(request, edicion_id):
    """ED2: edición de una edición y sus datos."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    form = EdicionForm(data=request.POST or None, instance=edicion)

    if request.method == 'POST' and form.is_valid():
        form.save()
        registrar_evento(request, 'ediciones', 'edicion_actualizada', {'id': edicion_id})
        messages.success(request, f'Edición «{edicion}» actualizada.')
        return _volver(request, 'gestion:ediciones')

    return render(
        request,
        'gestion/edicion_form.html',
        {
            'form': form,
            'titulo': f'Editar {edicion}',
            'edicion': edicion,
            'siguiente': _siguiente(request),
        },
    )


@requiere_permiso('ediciones.ver')
def edicion_gestionar(request, edicion_id):
    """Panel de una edición: sus categorías, votaciones y acciones.

    Una categoría forma parte de la edición cuando la edición tiene al menos
    una votación en ella. Desde aquí se agregan categorías (creando su
    votación) y se quitan las que aún no tienen votos.
    """
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    puede_agregar = tiene_permiso(request.user, 'votaciones.crear')
    puede_crear_categoria = tiene_permiso(request.user, 'categorias.crear')

    form = None
    if puede_agregar:
        form = EdicionCategoriaForm(
            data=request.POST or None,
            edicion=edicion,
            puede_crear_categoria=puede_crear_categoria,
        )
        if request.method == 'POST' and form.is_valid():
            datos = form.cleaned_data
            with transaction.atomic():
                categoria = datos['categoria']
                if categoria is None:
                    categoria = Categoria.objects.create(nombre=datos['nueva_categoria'])
                    registrar_evento(
                        request, 'categorias', 'categoria_creada', {'id': categoria.id}
                    )
                votacion = Votacion.objects.create(
                    edicion=edicion,
                    categoria=categoria,
                    nombre=datos['nombre_votacion'].strip(),
                    fecha_apertura=datos['fecha_apertura'],
                    fecha_cierre=datos['fecha_cierre'],
                    estado='BORRADOR',
                    mostrar_resultados_en_vivo=True,
                )
            registrar_evento(request, 'votaciones', 'votacion_creada', {'id': votacion.id})
            messages.success(
                request,
                f'«{categoria.nombre}» ya forma parte de {edicion}. Agrega las '
                f'opciones de «{votacion.nombre}» y ábrela cuando esté lista.',
            )
            return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    votaciones = list(
        edicion.votaciones.select_related('categoria')
        .annotate(
            num_votos=Count('opciones__votos', distinct=True),
            num_opciones=Count('opciones', distinct=True),
        )
        .order_by('categoria__nombre', 'nombre')
    )

    return render(
        request,
        'gestion/edicion_gestionar.html',
        {
            'edicion': edicion,
            'votaciones': votaciones,
            'num_categorias': len({v.categoria_id for v in votaciones}),
            'total_votos': sum(v.num_votos for v in votaciones),
            'form': form,
            'puede_editar': tiene_permiso(request.user, 'ediciones.editar'),
            'puede_editar_votaciones': tiene_permiso(request.user, 'votaciones.editar'),
            'puede_quitar': tiene_permiso(request.user, 'votaciones.eliminar'),
        },
    )


@requiere_permiso('votaciones.eliminar')
def edicion_quitar_categoria(request, edicion_id, categoria_id):
    """Quita una categoría de la edición borrando sus votaciones.

    Se bloquea si alguna de esas votaciones ya tiene votos: el conteo debe
    conservarse. La categoría en sí no se borra; sigue disponible para otras
    ediciones.
    """
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    votaciones = list(edicion.votaciones.filter(categoria=categoria))
    con_votos = [v for v in votaciones if v.total_votos > 0]

    if not votaciones:
        messages.warning(request, f'«{categoria.nombre}» no forma parte de {edicion}.')
        return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    if request.method == 'POST':
        if con_votos:
            messages.error(
                request,
                f'No se puede quitar «{categoria.nombre}»: sus votaciones ya '
                'registran votos.',
            )
        else:
            for votacion in votaciones:
                votacion.delete()
            registrar_evento(
                request,
                'ediciones',
                'categoria_quitada',
                {'edicion': edicion.id, 'categoria': categoria.id},
            )
            messages.success(request, f'«{categoria.nombre}» se quitó de {edicion}.')
        return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    return render(
        request,
        'gestion/edicion_quitar_categoria.html',
        {
            'edicion': edicion,
            'categoria': categoria,
            'votaciones': votaciones,
            'con_votos': con_votos,
        },
    )


@requiere_permiso('ediciones.eliminar')
def edicion_eliminar(request, edicion_id):
    """ED3: confirmación previa y bloqueo si hay votos en sus votaciones."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    con_votos = [v for v in edicion.votaciones.all() if v.total_votos > 0]

    if request.method == 'POST':
        if con_votos:
            nombres = ', '.join(v.nombre for v in con_votos)
            messages.error(
                request,
                f'No se puede eliminar «{edicion}»: la(s) votacion(es) '
                f'{nombres} ya registran votos.',
            )
            return redirect('gestion:ediciones')

        nombre = str(edicion)
        edicion.delete()
        registrar_evento(request, 'ediciones', 'edicion_eliminada', {'id': edicion_id})
        messages.success(request, f'Edición «{nombre}» eliminada.')
        return redirect('gestion:ediciones')

    return render(
        request,
        'gestion/edicion_confirmar_borrar.html',
        {'objeto': edicion, 'con_votos': con_votos},
    )


@requiere_permiso('ediciones.editar')
def edicion_publicar(request, edicion_id):
    """ED4: BORRADOR/PROGRAMADA → ACTIVA (solo por POST)."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)

    if request.method == 'POST':
        if edicion.estado == 'FINALIZADA':
            messages.error(request, 'Una edición FINALIZADA no cambia de estado.')
        elif edicion.estado in ('BORRADOR', 'PROGRAMADA'):
            edicion.estado = 'ACTIVA'
            edicion.save(update_fields=['estado'])
            registrar_evento(request, 'ediciones', 'edicion_publicada', {'id': edicion_id})
            messages.success(request, f'Edición «{edicion}» publicada (ACTIVA).')
        else:
            messages.warning(request, f'La edición ya está en estado {edicion.estado}.')

    return _volver(request, 'gestion:ediciones')


@requiere_permiso('ediciones.editar')
def edicion_finalizar(request, edicion_id):
    """ED4: cierre definitivo; desde FINALIZADA no retrocede."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)

    if request.method == 'POST':
        if edicion.estado == 'FINALIZADA':
            messages.warning(request, f'La edición «{edicion}» ya está FINALIZADA.')
        else:
            edicion.estado = 'FINALIZADA'
            edicion.save(update_fields=['estado'])
            registrar_evento(request, 'ediciones', 'edicion_finalizada', {'id': edicion_id})
            messages.success(request, f'Edición «{edicion}» finalizada.')

    return _volver(request, 'gestion:ediciones')


# --------------------------------------------------------------------------
# Categorías (CA1, CA2, CA3)
# --------------------------------------------------------------------------

@requiere_permiso('categorias.ver')
def categoria_lista(request):
    """CA1: muestra cuántas votaciones usan cada categoría."""
    return render(
        request,
        'gestion/categoria_lista.html',
        {
            'categorias': Categoria.objects.annotate(
                num_votaciones=Count('votaciones')
            ),
            'puede_crear': tiene_permiso(request.user, 'categorias.crear'),
        },
    )


@requiere_permiso('categorias.crear')
def categoria_crear(request):
    """CA2: alta; nombre único con error legible en el formulario."""
    form = CategoriaForm(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        categoria = form.save()
        registrar_evento(request, 'categorias', 'categoria_creada', {'id': categoria.id})
        messages.success(request, f'Categoría «{categoria.nombre}» creada.')
        return redirect('gestion:categorias')

    return render(request, 'gestion/categoria_form.html', {'form': form, 'titulo': 'Nueva categoría'})


@requiere_permiso('categorias.editar')
def categoria_editar(request, categoria_id):
    """CA2: edición; el duplicado revienta en el formulario, no en la BD."""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    form = CategoriaForm(data=request.POST or None, instance=categoria)

    if request.method == 'POST' and form.is_valid():
        form.save()
        registrar_evento(request, 'categorias', 'categoria_actualizada', {'id': categoria_id})
        messages.success(request, f'Categoría «{categoria.nombre}» actualizada.')
        return redirect('gestion:categorias')

    return render(
        request,
        'gestion/categoria_form.html',
        {'form': form, 'titulo': f'Editar {categoria.nombre}', 'categoria': categoria},
    )


@requiere_permiso('categorias.eliminar')
def categoria_eliminar(request, categoria_id):
    """CA3: bloquea el borrado si alguna votación la usa, con el motivo."""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    usos = categoria.votaciones.all()

    if request.method == 'POST':
        if usos.exists():
            nombres = ', '.join(v.nombre for v in usos[:5])
            messages.error(
                request,
                f'No se puede eliminar «{categoria.nombre}»: la usan '
                f'{usos.count()} votación(es): {nombres}.',
            )
            return redirect('gestion:categorias')

        nombre = categoria.nombre
        categoria.delete()
        registrar_evento(request, 'categorias', 'categoria_eliminada', {'id': categoria_id})
        messages.success(request, f'Categoría «{nombre}» eliminada.')
        return redirect('gestion:categorias')

    return render(
        request,
        'gestion/categoria_confirmar_borrar.html',
        {'objeto': categoria, 'usos': usos},
    )


# --------------------------------------------------------------------------
# Votaciones (VO1, VO2, VO3, VO5)
# --------------------------------------------------------------------------
# VO4 (control de apertura) vive en el tarjetón: votacion.esta_abierta exige
# estado=ACTIVA y la fecha actual dentro del rango; lo prueba el test de
# 'votacion cerrada' y el nuevo test de apertura fuera de rango.

@requiere_permiso('votaciones.ver')
def votacion_lista(request):
    """VO1: listado filtrable por edición y categoría, con total de votos."""
    votaciones = (
        Votacion.objects.select_related('edicion', 'categoria')
        .annotate(num_votos=Count('opciones__votos'))
        .order_by('-fecha_apertura')
    )

    filtro_edicion = request.GET.get('edicion') or ''
    filtro_categoria = request.GET.get('categoria') or ''
    if filtro_edicion.isdigit():
        votaciones = votaciones.filter(edicion_id=filtro_edicion)
    if filtro_categoria.isdigit():
        votaciones = votaciones.filter(categoria_id=filtro_categoria)

    return render(
        request,
        'gestion/votacion_lista.html',
        {
            'votaciones': votaciones,
            'ediciones': Edicion.objects.order_by('-anio', 'nombre'),
            'categorias': Categoria.objects.order_by('nombre'),
            'filtro_edicion': filtro_edicion,
            'filtro_categoria': filtro_categoria,
            'puede_crear': tiene_permiso(request.user, 'votaciones.crear'),
        },
    )


@requiere_permiso('votaciones.crear')
def votacion_crear(request):
    """VO2: alta con selects de edición y categoría.

    ``?edicion=`` y ``?categoria=`` preseleccionan los selects cuando se
    llega desde el panel de una edición.
    """
    inicial = {
        campo: request.GET[campo]
        for campo in ('edicion', 'categoria')
        if request.GET.get(campo, '').isdigit()
    }
    form = VotacionForm(data=request.POST or None, initial=inicial)

    if request.method == 'POST' and form.is_valid():
        votacion = form.save()
        registrar_evento(request, 'votaciones', 'votacion_creada', {'id': votacion.id})
        messages.success(request, f'Votación «{votacion.nombre}» creada.')
        return _volver(request, 'gestion:votaciones')

    return render(
        request,
        'gestion/votacion_form.html',
        {'form': form, 'titulo': 'Nueva votación', 'siguiente': _siguiente(request)},
    )


@requiere_permiso('votaciones.editar')
def votacion_editar(request, votacion_id):
    """VO2 + VO3: edición y validación de fechas."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    form = VotacionForm(data=request.POST or None, instance=votacion)

    if request.method == 'POST' and form.is_valid():
        form.save()
        registrar_evento(request, 'votaciones', 'votacion_actualizada', {'id': votacion_id})
        messages.success(request, f'Votación «{votacion.nombre}» actualizada.')
        return _volver(request, 'gestion:votaciones')

    return render(
        request,
        'gestion/votacion_form.html',
        {
            'form': form,
            'titulo': f'Editar {votacion}',
            'votacion': votacion,
            'siguiente': _siguiente(request),
        },
    )


@requiere_permiso('votaciones.editar')
def votacion_abrir(request, votacion_id):
    """VO5: BORRADOR/PROGRAMADA → ACTIVA (solo por POST)."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)

    if request.method == 'POST':
        if votacion.estado == 'FINALIZADA':
            messages.error(request, 'Una votación FINALIZADA no se reabre.')
        elif votacion.estado in ('BORRADOR', 'PROGRAMADA'):
            votacion.estado = 'ACTIVA'
            votacion.save(update_fields=['estado'])
            registrar_evento(request, 'votaciones', 'votacion_abierta', {'id': votacion_id})
            messages.success(request, f'Votación «{votacion.nombre}» abierta (ACTIVA).')
        else:
            messages.warning(request, f'La votación ya está en estado {votacion.estado}.')

    return _volver(request, 'gestion:votaciones')


@requiere_permiso('votaciones.editar')
def votacion_cerrar(request, votacion_id):
    """VO5: cierre definitivo; no borra votos y habilita resultados."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)

    if request.method == 'POST':
        if votacion.estado == 'FINALIZADA':
            messages.warning(request, f'La votación «{votacion.nombre}» ya está FINALIZADA.')
        else:
            votacion.estado = 'FINALIZADA'
            votacion.save(update_fields=['estado'])
            registrar_evento(request, 'votaciones', 'votacion_cerrada', {'id': votacion_id})
            total = votacion.total_votos
            messages.success(
                request,
                f'Votación «{votacion.nombre}» cerrada. Sus {total} voto(s) se '
                'conservan y los resultados quedan visibles.',
            )

    return _volver(request, 'gestion:votaciones')


# --------------------------------------------------------------------------
# Opciones dentro de una votación (OP1, OP2, OP3)
# --------------------------------------------------------------------------

@requiere_permiso('opciones.ver')
def opcion_lista(request, votacion_id):
    """OP1: opciones de la votación ordenadas por casilla, con votos."""
    votacion = get_object_or_404(
        Votacion.objects.select_related('edicion', 'categoria'), pk=votacion_id
    )

    return render(
        request,
        'gestion/opcion_lista.html',
        {
            'votacion': votacion,
            'opciones': (
                Opcion.objects.filter(votacion=votacion)
                .annotate(num_votos=Count('votos'))
                .order_by('orden', 'nombre')
            ),
            'puede_crear': tiene_permiso(request.user, 'opciones.crear'),
        },
    )


@requiere_permiso('opciones.crear')
def opcion_crear(request, votacion_id):
    """OP2: alta de opción con casilla única en la votación."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    form = OpcionForm(data=request.POST or None, votacion=votacion)

    if request.method == 'POST' and form.is_valid():
        opcion = form.save(commit=False)
        opcion.votacion = votacion
        opcion.save()
        registrar_evento(request, 'opciones', 'opcion_creada', {'id': opcion.id, 'votacion': votacion.id})
        messages.success(request, f'Opción «{opcion.nombre}» creada.')
        return redirect('gestion:opcion_lista', votacion_id=votacion.id)

    return render(
        request,
        'gestion/opcion_form.html',
        {
            'form': form,
            'votacion': votacion,
            'titulo': f'Nueva opción en «{votacion.nombre}»',
        },
    )


@requiere_permiso('opciones.editar')
def opcion_editar(request, votacion_id, opcion_id):
    """OP2: edición con la casilla única por votación."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    opcion = get_object_or_404(Opcion, pk=opcion_id, votacion=votacion)
    form = OpcionForm(data=request.POST or None, instance=opcion, votacion=votacion)

    if request.method == 'POST' and form.is_valid():
        form.save()
        registrar_evento(request, 'opciones', 'opcion_actualizada', {'id': opcion_id, 'votacion': votacion.id})
        messages.success(request, f'Opción «{opcion.nombre}» actualizada.')
        return redirect('gestion:opcion_lista', votacion_id=votacion.id)

    return render(
        request,
        'gestion/opcion_form.html',
        {
            'form': form,
            'votacion': votacion,
            'titulo': f'Editar {opcion.nombre}',
        },
    )


@requiere_permiso('opciones.eliminar')
def opcion_eliminar(request, votacion_id, opcion_id):
    """OP3: bloquea el borrado si la opción ya tiene votos."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    opcion = get_object_or_404(Opcion, pk=opcion_id, votacion=votacion)

    if request.method == 'POST':
        if opcion.votos.exists():
            messages.error(
                request,
                f'No se puede eliminar «{opcion.nombre}»: ya registró '
                f'{opcion.votos.count()} voto(s) y el conteo debe conservarse.',
            )
            return redirect('gestion:opcion_lista', votacion_id=votacion.id)

        nombre = opcion.nombre
        opcion.delete()
        registrar_evento(request, 'opciones', 'opcion_eliminada', {'id': opcion_id, 'votacion': votacion.id})
        messages.success(request, f'Opción «{nombre}» eliminada.')
        return redirect('gestion:opcion_lista', votacion_id=votacion.id)

    return render(
        request,
        'gestion/opcion_confirmar_borrar.html',
        {'votacion': votacion, 'opcion': opcion},
    )
