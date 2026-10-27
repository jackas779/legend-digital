"""Gestión de Ediciones y Categorías por el sitio MVT (ED1-ED4, CA1-CA3).

Toda la gestión exige permisos del catálogo vía ``@requiere_permiso``; el
bloqueo de borrados y las transiciones de estado se validan aquí.
"""

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from back.apps.usuarios.permisos import requiere_permiso, tiene_permiso

from .gestion_forms import CategoriaForm, EdicionForm
from .models import Categoria, Edicion


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
        messages.success(request, f'Edición «{edicion}» actualizada.')
        return redirect('gestion:ediciones')

    return render(
        request,
        'gestion/edicion_form.html',
        {'form': form, 'titulo': f'Editar {edicion}', 'edicion': edicion},
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
            messages.success(request, f'Edición «{edicion}» publicada (ACTIVA).')
        else:
            messages.warning(request, f'La edición ya está en estado {edicion.estado}.')

    return redirect('gestion:ediciones')


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
            messages.success(request, f'Edición «{edicion}» finalizada.')

    return redirect('gestion:ediciones')


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
        messages.success(request, f'Categoría «{nombre}» eliminada.')
        return redirect('gestion:categorias')

    return render(
        request,
        'gestion/categoria_confirmar_borrar.html',
        {'objeto': categoria, 'usos': usos},
    )
