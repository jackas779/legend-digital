"""Gestión de Ediciones, Categorías, Votaciones y Opciones por el sitio MVT.

Toda la gestión exige permisos del catálogo vía ``@requiere_permiso``. Los
cambios de estado no se hacen aquí: se piden a ``elecciones.ciclo``, que
aplica las reglas (validación al programar, cierre en cascada, escrutinio
y finalización automática). Aquí solo se decide qué se puede editar según
el estado de la edición.
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from back.apps.auditoria.servicio import registrar_evento
from back.apps.usuarios.permisos import requiere_permiso, tiene_permiso

from . import ciclo
from .gestion_forms import (
    CategoriaForm,
    CierreAnticipadoForm,
    EdicionCategoriaForm,
    EdicionForm,
    EmpateForm,
    InscripcionListaForm,
    NormativaForm,
    OpcionForm,
    RondaSiguienteForm,
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


def _informar_transicion_invalida(request, error):
    messages.error(request, str(error))
    for detalle in error.errores:
        messages.warning(request, detalle)


# --------------------------------------------------------------------------
# Ediciones (ED1, ED2, ED3, ED4)
# --------------------------------------------------------------------------

@requiere_permiso('ediciones.ver')
def edicion_lista(request):
    """ED1: nombre, año, estado, periodo y cantidad de votaciones."""
    return render(
        request,
        'gestion/edicion_lista.html',
        {
            'ediciones': (
                Edicion.objects.annotate(
                    num_votaciones=Count('votaciones', distinct=True),
                    num_pendientes=Count(
                        'discrepancias',
                        filter=Q(discrepancias__estado='ABIERTA'),
                        distinct=True,
                    ),
                )
                .order_by('-anio', 'nombre')
            ),
            'puede_crear': tiene_permiso(request.user, 'ediciones.crear'),
            'puede_editar': tiene_permiso(request.user, 'ediciones.editar'),
            'puede_eliminar': tiene_permiso(request.user, 'ediciones.eliminar'),
        },
    )


@requiere_permiso('ediciones.crear')
def edicion_crear(request):
    """ED2: alta de una edición; siempre nace en BORRADOR."""
    form = EdicionForm(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        edicion = form.save(commit=False)
        edicion.creador = getattr(request.user, 'perfil_usuario', None)
        edicion.save()
        registrar_evento(request, 'ediciones', 'edicion_creada', {'id': edicion.id})
        messages.success(
            request,
            f'Edición «{edicion}» creada en borrador. Agrega sus categorías y '
            'prográmala cuando esté lista.',
        )
        return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    return render(request, 'gestion/edicion_form.html', {'form': form, 'titulo': 'Nueva edición'})


@requiere_permiso('ediciones.editar')
def edicion_editar(request, edicion_id):
    """ED2: en BORRADOR se edita todo; después, solo el nombre."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    if edicion.estado in (Edicion.ACTIVA, Edicion.CERRANDO, Edicion.FINALIZADA):
        messages.warning(
            request,
            f'La edición está {edicion.get_estado_display().upper()}: sus datos ya no se editan.',
        )
        return _volver(request, 'gestion:edicion_gestionar', edicion.id)

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
    """Panel de una edición: estado, periodo, categorías, votaciones y acciones.

    Una categoría forma parte de la edición cuando la edición tiene al menos
    una votación en ella. Las categorías solo se agregan y quitan con la
    edición en BORRADOR.
    """
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    en_borrador = edicion.admite_cambios_de_estructura
    puede_agregar = en_borrador and tiene_permiso(request.user, 'votaciones.crear')
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
                    estado=Votacion.BORRADOR,
                )
            registrar_evento(request, 'votaciones', 'votacion_creada', {'id': votacion.id})
            messages.success(
                request,
                f'«{categoria.nombre}» ya forma parte de {edicion}. Agrega las '
                f'opciones de «{votacion.nombre}»; se abrirá sola en su fecha '
                'cuando la edición esté programada.',
            )
            return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    votaciones = list(
        edicion.votaciones.select_related('categoria', 'ronda_anterior', 'opcion_ganadora')
        .annotate(
            num_votos=Count('opciones__votos', distinct=True),
            num_opciones=Count('opciones', distinct=True),
            num_validas=Count(
                'opciones', filter=Q(opciones__es_voto_blanco=False), distinct=True
            ),
        )
        .order_by('categoria__nombre', 'numero_ronda', 'nombre')
    )
    con_siguiente = {v.ronda_anterior_id for v in votaciones if v.ronda_anterior_id}
    for votacion in votaciones:
        votacion.tiene_siguiente = votacion.pk in con_siguiente
        votacion.falta_siguiente = votacion.necesita_ronda_siguiente and not votacion.tiene_siguiente
        # Empate sin resolver: la ronda siguiente (si existe) espera la decisión.
        votacion.empate_pendiente = (
            votacion.resultado == Votacion.EMPATE and not votacion.decision_empate
        )

    puede_editar = tiene_permiso(request.user, 'ediciones.editar')
    return render(
        request,
        'gestion/edicion_gestionar.html',
        {
            'edicion': edicion,
            'votaciones': votaciones,
            'pasos': _pasos(edicion),
            'num_categorias': len({v.categoria_id for v in votaciones}),
            'total_votos': sum(v.num_votos for v in votaciones),
            'num_por_escrutar': sum(1 for v in votaciones if v.estado == Votacion.CERRADA),
            'num_inscritos': edicion.inscripciones.count(),
            'usa_inscripcion': any(v.solo_inscritos for v in votaciones),
            'form': form,
            'en_borrador': en_borrador,
            # Qué le falta para programarse, para mostrarlo antes de intentarlo.
            'pendientes_programar': (
                ciclo.errores_para_programar(edicion) if en_borrador else []
            ),
            'puede_editar': puede_editar,
            'puede_editar_datos': puede_editar and edicion.estado in (
                Edicion.BORRADOR, Edicion.PROGRAMADA
            ),
            'puede_editar_votaciones': tiene_permiso(request.user, 'votaciones.editar'),
            'puede_quitar': en_borrador and tiene_permiso(request.user, 'votaciones.eliminar'),
        },
    )


def _pasos(edicion):
    """Barra de pasos del ciclo de vida: hecho / actual / pendiente."""
    orden = [e for e, _ in Edicion.ESTADOS]
    actual = orden.index(edicion.estado)
    return [
        {
            'nombre': nombre,
            'estado': 'hecho' if i < actual else 'actual' if i == actual else 'pendiente',
        }
        for i, (_, nombre) in enumerate(Edicion.ESTADOS)
    ]


@requiere_permiso('votaciones.eliminar')
def edicion_quitar_categoria(request, edicion_id, categoria_id):
    """Quita una categoría de la edición borrando sus votaciones.

    Solo con la edición en BORRADOR (la estructura se fija al programar) y
    nunca si alguna de esas votaciones tiene votos. La categoría en sí no se
    borra: sigue disponible para otras ediciones.
    """
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    # Las rondas posteriores primero: una ronda no se borra antes que la que la sigue.
    votaciones = list(edicion.votaciones.filter(categoria=categoria).order_by('-numero_ronda'))
    con_votos = [v for v in votaciones if v.total_votos > 0]
    volver = redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    if not votaciones:
        messages.warning(request, f'«{categoria.nombre}» no forma parte de {edicion}.')
        return volver

    if not edicion.admite_cambios_de_estructura:
        messages.error(
            request,
            f'La edición está {edicion.get_estado_display().upper()}: las categorías '
            'solo se quitan en BORRADOR.',
        )
        return volver

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
        return volver

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
    """ED3: solo en BORRADOR o PROGRAMADA y sin votos (nunca hubo votación)."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    con_votos = [v for v in edicion.votaciones.all() if v.total_votos > 0]
    # Con discrepancias registradas hay historial de auditoría que conservar.
    bloqueada_por_estado = (
        edicion.estado not in (Edicion.BORRADOR, Edicion.PROGRAMADA)
        or edicion.discrepancias.exists()
    )

    if request.method == 'POST':
        if bloqueada_por_estado:
            messages.error(
                request,
                f'No se puede eliminar «{edicion}»: está '
                f'{edicion.get_estado_display().upper()} y su historial se conserva.',
            )
            return redirect('gestion:ediciones')
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
        {
            'objeto': edicion,
            'con_votos': con_votos,
            'bloqueada_por_estado': bloqueada_por_estado,
        },
    )


@requiere_permiso('ediciones.editar')
def edicion_programar(request, edicion_id):
    """BORRADOR → PROGRAMADA, con validación completa (solo por POST)."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)

    if request.method == 'POST':
        try:
            ciclo.programar(edicion, request)
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            if edicion.estado == Edicion.ACTIVA:
                messages.success(
                    request,
                    f'Edición «{edicion}» programada y ya ACTIVA: su fecha de inicio llegó.',
                )
            else:
                inicio = timezone.localtime(edicion.fecha_inicio)
                messages.success(
                    request,
                    f'Edición «{edicion}» programada. Se activará sola el '
                    f'{inicio:%d/%m/%Y a las %H:%M}.',
                )

    return _volver(request, 'gestion:edicion_gestionar', edicion.id)


@requiere_permiso('ediciones.editar')
def edicion_desprogramar(request, edicion_id):
    """PROGRAMADA → BORRADOR para corregir (solo por POST)."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)

    if request.method == 'POST':
        try:
            ciclo.desprogramar(edicion, request)
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            messages.success(request, f'Edición «{edicion}» devuelta a borrador.')

    return _volver(request, 'gestion:edicion_gestionar', edicion.id)


@requiere_permiso('ediciones.editar')
def edicion_cerrar(request, edicion_id):
    """Cierre anticipado: ACTIVA → CERRANDO con motivo obligatorio."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    if edicion.estado != Edicion.ACTIVA:
        messages.warning(
            request,
            f'Solo se cierra anticipadamente una edición ACTIVA; esta está '
            f'{edicion.get_estado_display().upper()}.',
        )
        return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    form = CierreAnticipadoForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            ciclo.cerrar(
                edicion, request, motivo=form.cleaned_data['motivo'], anticipado=True
            )
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            messages.success(
                request,
                f'Edición «{edicion}» cerrada anticipadamente. Ya no recibe votos; '
                'escruta sus votaciones para finalizarla.',
            )
        return redirect('gestion:edicion_gestionar', edicion_id=edicion.id)

    return render(
        request,
        'gestion/edicion_cerrar.html',
        {
            'edicion': edicion,
            'form': form,
            'abiertas': edicion.votaciones.filter(estado=Votacion.ABIERTA),
            'sin_abrir': edicion.votaciones.filter(
                estado__in=(Votacion.BORRADOR, Votacion.LISTA)
            ),
        },
    )


@requiere_permiso('ediciones.editar')
def edicion_escrutar(request, edicion_id):
    """Genera el acta de cada votación CERRADA (solo por POST).

    Cuando ya no queda nada por escrutar, la edición en escrutinio pasa
    sola a FINALIZADA.
    """
    edicion = get_object_or_404(Edicion, pk=edicion_id)

    if request.method == 'POST':
        escrutadas = ciclo.escrutar_edicion(edicion, request)
        if not escrutadas:
            messages.info(request, 'No hay votaciones cerradas pendientes de escrutinio.')
        elif edicion.estado == Edicion.FINALIZADA:
            messages.success(
                request,
                f'{escrutadas} votación(es) escrutada(s). La edición «{edicion}» quedó FINALIZADA.',
            )
        else:
            messages.success(request, f'{escrutadas} votación(es) escrutada(s).')

    return _volver(request, 'gestion:edicion_gestionar', edicion.id)


# --------------------------------------------------------------------------
# Categorías (CA1, CA2, CA3)
# --------------------------------------------------------------------------

@requiere_permiso('categorias.ver')
def categoria_lista(request):
    """CA1: catálogo global con usos; las archivadas van al final."""
    return render(
        request,
        'gestion/categoria_lista.html',
        {
            'categorias': Categoria.objects.annotate(
                num_votaciones=Count('votaciones', distinct=True),
                num_ediciones=Count('votaciones__edicion', distinct=True),
            ).order_by('archivada', 'nombre'),
            'puede_crear': tiene_permiso(request.user, 'categorias.crear'),
            'puede_editar': tiene_permiso(request.user, 'categorias.editar'),
        },
    )


@requiere_permiso('categorias.crear')
def categoria_crear(request):
    """CA2: alta de categoría con validación de nombre único."""
    form = CategoriaForm(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        categoria = form.save()
        registrar_evento(request, 'categorias', 'categoria_creada', {'id': categoria.id})
        messages.success(request, f'Categoría «{categoria.nombre}» creada.')
        return redirect('gestion:categorias')

    return render(request, 'gestion/categoria_form.html', {'form': form, 'titulo': 'Nueva categoría'})


@requiere_permiso('categorias.editar')
def categoria_editar(request, categoria_id):
    """CA2: edición; el nombre queda fijo si ya se usó en una edición finalizada."""
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


@requiere_permiso('categorias.editar')
def categoria_archivar(request, categoria_id):
    """Archiva o reactiva una categoría (solo por POST).

    Archivada deja de ofrecerse a ediciones nuevas, pero sigue apareciendo
    en las ediciones donde ya se usó.
    """
    categoria = get_object_or_404(Categoria, pk=categoria_id)

    if request.method == 'POST':
        categoria.archivada = not categoria.archivada
        categoria.save(update_fields=['archivada'])
        accion = 'categoria_archivada' if categoria.archivada else 'categoria_reactivada'
        registrar_evento(request, 'categorias', accion, {'id': categoria.id})
        if categoria.archivada:
            messages.success(
                request,
                f'«{categoria.nombre}» archivada: ya no se ofrece a ediciones nuevas.',
            )
        else:
            messages.success(request, f'«{categoria.nombre}» vuelve a estar disponible.')

    return redirect('gestion:categorias')


@requiere_permiso('categorias.eliminar')
def categoria_eliminar(request, categoria_id):
    """CA3: confirmación y bloqueo si alguna votación la usa (se archiva)."""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    usos = categoria.votaciones.all()

    if request.method == 'POST':
        if usos.exists():
            messages.error(
                request,
                f'No se puede eliminar «{categoria.nombre}»: la usan '
                f'{usos.count()} votación(es). Archívala para dejar de ofrecerla.',
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
# estado ABIERTA, la fecha actual dentro de su ventana y la edición ACTIVA
# dentro de su periodo.

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
            'puede_editar': tiene_permiso(request.user, 'votaciones.editar'),
        },
    )


@requiere_permiso('votaciones.crear')
def votacion_crear(request):
    """VO2: alta en una edición en BORRADOR; la votación nace en BORRADOR.

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
        votacion = form.save(commit=False)
        votacion.estado = Votacion.BORRADOR
        votacion.save()
        registrar_evento(request, 'votaciones', 'votacion_creada', {'id': votacion.id})
        messages.success(request, f'Votación «{votacion.nombre}» creada en borrador.')
        return _volver(request, 'gestion:votaciones')

    return render(
        request,
        'gestion/votacion_form.html',
        {'form': form, 'titulo': 'Nueva votación', 'siguiente': _siguiente(request)},
    )


@requiere_permiso('votaciones.editar')
def votacion_editar(request, votacion_id):
    """VO2 + VO3: edición según el estado; las votaciones terminadas no se tocan."""
    votacion = get_object_or_404(Votacion.objects.select_related('edicion'), pk=votacion_id)
    if votacion.es_final or votacion.edicion.es_solo_lectura:
        messages.warning(
            request,
            f'La votación está {votacion.get_estado_display().upper()}: ya no se edita.',
        )
        return _volver(request, 'gestion:votaciones')

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
    """VO5: apertura adelantada LISTA → ABIERTA, solo con la edición ACTIVA."""
    votacion = get_object_or_404(Votacion.objects.select_related('edicion'), pk=votacion_id)

    if request.method == 'POST':
        try:
            ciclo.abrir_votacion(votacion, request)
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            messages.success(request, f'Votación «{votacion.nombre}» abierta.')

    return _volver(request, 'gestion:votaciones')


@requiere_permiso('votaciones.editar')
def votacion_cerrar(request, votacion_id):
    """VO5: cierre ABIERTA → CERRADA; no borra votos y no se reabre."""
    votacion = get_object_or_404(Votacion.objects.select_related('edicion'), pk=votacion_id)

    if request.method == 'POST':
        try:
            ciclo.cerrar_votacion(votacion, request)
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            messages.success(
                request,
                f'Votación «{votacion.nombre}» cerrada. Sus {votacion.total_votos} '
                'voto(s) se conservan y queda pendiente de escrutinio.',
            )

    return _volver(request, 'gestion:votaciones')


# --------------------------------------------------------------------------
# Opciones dentro de una votación (OP1, OP2, OP3)
# --------------------------------------------------------------------------
# Se agregan y quitan solo con la votación en BORRADOR (edición en borrador);
# con la votación LISTA se corrigen textos; abierta o terminada, nada.

def _opciones_bloqueadas(request, votacion, accion):
    messages.error(
        request,
        f'No se puede {accion} opciones: la votación está '
        f'{votacion.get_estado_display().upper()}.',
    )
    return redirect('gestion:opcion_lista', votacion_id=votacion.id)


@requiere_permiso('opciones.ver')
def opcion_lista(request, votacion_id):
    """OP1: opciones de la votación ordenadas por casilla, con votos."""
    votacion = get_object_or_404(
        Votacion.objects.select_related('edicion', 'categoria', 'ronda_anterior'), pk=votacion_id
    )
    en_borrador = votacion.admite_opciones_nuevas

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
            'puede_crear': en_borrador and tiene_permiso(request.user, 'opciones.crear'),
            'puede_editar': (
                votacion.estado in (Votacion.BORRADOR, Votacion.LISTA)
                and tiene_permiso(request.user, 'opciones.editar')
            ),
            'puede_eliminar': en_borrador and tiene_permiso(request.user, 'opciones.eliminar'),
        },
    )


@requiere_permiso('opciones.crear')
def opcion_crear(request, votacion_id):
    """OP2: alta de opción con casilla única en la votación."""
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    if not votacion.admite_opciones_nuevas:
        return _opciones_bloqueadas(request, votacion, 'agregar')

    form = OpcionForm(data=request.POST or None, files=request.FILES or None, votacion=votacion)

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
    if votacion.estado not in (Votacion.BORRADOR, Votacion.LISTA):
        return _opciones_bloqueadas(request, votacion, 'editar')

    form = OpcionForm(
        data=request.POST or None, files=request.FILES or None, instance=opcion, votacion=votacion
    )

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
    """OP3: solo en BORRADOR y nunca si la opción ya tiene votos."""
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
        if not votacion.admite_opciones_nuevas:
            return _opciones_bloqueadas(request, votacion, 'eliminar')

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


# --------------------------------------------------------------------------
# Rondas: ronda siguiente, preparación tras repetición y empates
# --------------------------------------------------------------------------

@requiere_permiso('votaciones.crear')
def ronda_siguiente_crear(request, votacion_id):
    """Configura de antemano la ronda que sigue (segunda vuelta, final o repetición).

    Solo con la edición en borrador: al programar, la estructura queda fija.
    """
    anterior = get_object_or_404(Votacion.objects.select_related('edicion', 'categoria'), pk=votacion_id)
    volver = redirect('gestion:edicion_gestionar', edicion_id=anterior.edicion_id)
    if not anterior.edicion.admite_cambios_de_estructura:
        messages.error(request, 'Las rondas se configuran con la edición en BORRADOR.')
        return volver
    if not anterior.necesita_ronda_siguiente:
        messages.error(
            request,
            f'«{anterior.nombre}» se decide por mayoría simple sin repetición: no lleva otra ronda.',
        )
        return volver
    if Votacion.objects.filter(ronda_anterior=anterior).exists():
        messages.info(request, f'«{anterior.nombre}» ya tiene su ronda siguiente.')
        return volver

    form = RondaSiguienteForm(data=request.POST or None, anterior=anterior)
    if request.method == 'POST' and form.is_valid():
        ronda = form.save(commit=False)
        ronda.edicion = anterior.edicion
        ronda.categoria = anterior.categoria
        ronda.ronda_anterior = anterior
        ronda.numero_ronda = anterior.numero_ronda + 1
        ronda.estado = Votacion.BORRADOR
        ronda.save()
        registrar_evento(
            request, 'votaciones', 'ronda_configurada',
            {'id': ronda.id, 'anterior': anterior.id},
        )
        messages.success(
            request,
            f'Ronda «{ronda.nombre}» configurada. Recibirá sus candidatos al escrutar '
            f'«{anterior.nombre}».',
        )
        return volver

    return render(
        request,
        'gestion/ronda_form.html',
        {'form': form, 'anterior': anterior, 'titulo': f'Ronda siguiente de «{anterior.nombre}»'},
    )


@requiere_permiso('votaciones.eliminar')
def ronda_eliminar(request, votacion_id):
    """Quita una ronda derivada (solo en borrador y si no alimenta otra)."""
    ronda = get_object_or_404(Votacion, pk=votacion_id)
    volver = redirect('gestion:edicion_gestionar', edicion_id=ronda.edicion_id)
    if request.method == 'POST':
        if not ronda.es_ronda_derivada or not ronda.edicion.admite_cambios_de_estructura:
            messages.error(request, 'Solo se quita una ronda derivada con la edición en BORRADOR.')
        elif Votacion.objects.filter(ronda_anterior=ronda).exists():
            messages.error(request, f'«{ronda.nombre}» alimenta otra ronda: quita primero esa.')
        else:
            nombre = ronda.nombre
            ronda.delete()
            registrar_evento(request, 'votaciones', 'ronda_eliminada', {'id': votacion_id})
            messages.success(request, f'Ronda «{nombre}» eliminada.')
    return volver


@requiere_permiso('votaciones.editar')
def ronda_preparar(request, votacion_id):
    """Tras una repetición: con los candidatos nuevos cargados, la ronda queda LISTA."""
    ronda = get_object_or_404(Votacion.objects.select_related('edicion'), pk=votacion_id)
    if request.method == 'POST':
        try:
            ciclo.preparar_ronda(ronda, request)
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            messages.success(request, f'Ronda «{ronda.nombre}» lista: se abrirá en su fecha.')
    return redirect('gestion:edicion_gestionar', edicion_id=ronda.edicion_id)


@requiere_permiso('votaciones.editar')
def empate_resolver(request, votacion_id):
    """El organizador decide un empate en el punto de corte (o una votación sin votos)."""
    votacion = get_object_or_404(Votacion.objects.select_related('edicion', 'categoria'), pk=votacion_id)
    volver = redirect('gestion:edicion_gestionar', edicion_id=votacion.edicion_id)
    if votacion.resultado != Votacion.EMPATE or votacion.decision_empate:
        messages.info(request, 'Esta votación no tiene un empate pendiente.')
        return volver

    necesarias = ciclo.cuantos_pasan(votacion)
    form = EmpateForm(data=request.POST or None, votacion=votacion, necesarias=necesarias)
    if request.method == 'POST' and form.is_valid():
        try:
            ciclo.resolver_empate(
                votacion, list(form.cleaned_data['opciones']), form.cleaned_data['motivo'], request
            )
        except ciclo.TransicionInvalida as error:
            _informar_transicion_invalida(request, error)
        else:
            messages.success(request, f'Empate de «{votacion.nombre}» resuelto.')
            return volver

    return render(
        request,
        'gestion/empate_form.html',
        {
            'votacion': votacion,
            'form': form,
            'conteo': ciclo.conteo(votacion),
            'detalle': ciclo.calcular_resultado(votacion)['detalle'],
            'necesarias': necesarias,
        },
    )


# --------------------------------------------------------------------------
# Inscripciones de una edición
# --------------------------------------------------------------------------

@requiere_permiso('inscripciones.gestionar')
def inscritos(request, edicion_id):
    """Lista de inscritos y carga por documentos."""
    from back.apps.votacion.inscripciones import (
        admite_inscripciones,
        inscribir_por_documentos,
    )

    edicion = get_object_or_404(Edicion, pk=edicion_id)
    form = InscripcionListaForm(data=request.POST or None)
    informe = None
    if request.method == 'POST' and form.is_valid():
        if not admite_inscripciones(edicion, por_organizador=True):
            messages.error(request, 'La edición ya no admite inscripciones.')
        else:
            informe = inscribir_por_documentos(request, edicion, form.cleaned_data['documentos'])
            messages.success(request, f'{len(informe["inscritos"])} votante(s) inscrito(s).')
            form = InscripcionListaForm()

    return render(
        request,
        'gestion/inscritos.html',
        {
            'edicion': edicion,
            'form': form,
            'informe': informe,
            'inscripciones': edicion.inscripciones.select_related(
                'usuario__perfil_usuario', 'inscrito_por'
            ),
            'admite': admite_inscripciones(edicion, por_organizador=True),
            'puede_retirar': edicion.estado in (Edicion.BORRADOR, Edicion.PROGRAMADA),
        },
    )


@requiere_permiso('inscripciones.gestionar')
def inscrito_retirar(request, edicion_id, inscripcion_id):
    from back.apps.votacion.inscripciones import InscripcionNoPermitida, desinscribir

    edicion = get_object_or_404(Edicion, pk=edicion_id)
    inscripcion = get_object_or_404(edicion.inscripciones, pk=inscripcion_id)
    if request.method == 'POST':
        try:
            desinscribir(request, edicion, inscripcion)
        except InscripcionNoPermitida as error:
            messages.error(request, str(error))
        else:
            messages.success(request, 'Inscripción retirada.')
    return redirect('gestion:inscritos', edicion_id=edicion.id)


# --------------------------------------------------------------------------
# Normativas (reglas) de una votación
# --------------------------------------------------------------------------

def _normativas_editables(votacion):
    return not votacion.edicion.es_solo_lectura


@requiere_permiso('votaciones.ver')
def normativa_lista(request, votacion_id):
    votacion = get_object_or_404(Votacion.objects.select_related('edicion', 'categoria'), pk=votacion_id)
    return render(
        request,
        'gestion/normativa_lista.html',
        {
            'votacion': votacion,
            'normativas': votacion.normativas.order_by('fecha_publicacion'),
            'puede_editar': (
                _normativas_editables(votacion) and tiene_permiso(request.user, 'votaciones.editar')
            ),
        },
    )


@requiere_permiso('votaciones.editar')
def normativa_form(request, votacion_id, normativa_id=None):
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    normativa = (
        get_object_or_404(votacion.normativas, pk=normativa_id) if normativa_id else None
    )
    if not _normativas_editables(votacion):
        messages.error(request, 'La edición está finalizada: sus normativas ya no cambian.')
        return redirect('gestion:normativa_lista', votacion_id=votacion.id)

    form = NormativaForm(data=request.POST or None, instance=normativa)
    if request.method == 'POST' and form.is_valid():
        nueva = form.save(commit=False)
        nueva.votacion = votacion
        nueva.save()
        registrar_evento(
            request, 'votaciones',
            'normativa_actualizada' if normativa else 'normativa_creada',
            {'id': nueva.id, 'votacion': votacion.id},
        )
        messages.success(request, f'Normativa «{nueva.titulo}» guardada.')
        return redirect('gestion:normativa_lista', votacion_id=votacion.id)

    return render(
        request,
        'gestion/normativa_form.html',
        {
            'form': form,
            'votacion': votacion,
            'titulo': f'Editar «{normativa.titulo}»' if normativa else 'Nueva normativa',
        },
    )


@requiere_permiso('votaciones.editar')
def normativa_eliminar(request, votacion_id, normativa_id):
    votacion = get_object_or_404(Votacion, pk=votacion_id)
    normativa = get_object_or_404(votacion.normativas, pk=normativa_id)
    if request.method == 'POST' and _normativas_editables(votacion):
        normativa.delete()
        registrar_evento(
            request, 'votaciones', 'normativa_eliminada',
            {'id': normativa_id, 'votacion': votacion.id},
        )
        messages.success(request, 'Normativa eliminada.')
    return redirect('gestion:normativa_lista', votacion_id=votacion.id)