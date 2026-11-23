"""Panel del auditor: verificación por edición y bandeja de discrepancias."""

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from back.apps.elecciones.models import Edicion, Votacion
from back.apps.usuarios.permisos import requiere_permiso, sin_permiso

from . import discrepancias as flujo
from .models import Discrepancia
from .verificacion import resumen_votaciones, verificar_edicion


@requiere_permiso('discrepancias.ver')
def ediciones(request):
    """Ediciones con su estado y discrepancias, para elegir qué verificar."""
    lista = (
        Edicion.objects.exclude(estado=Edicion.BORRADOR)
        .annotate(
            abiertas=Count(
                'discrepancias', filter=Q(discrepancias__estado=Discrepancia.ABIERTA), distinct=True
            ),
            total_discrepancias=Count('discrepancias', distinct=True),
            confirmaciones_total=Count('confirmaciones', distinct=True),
        )
        .order_by('-anio', 'nombre')
    )
    return render(request, 'auditoria/ediciones.html', {'ediciones': lista})


@requiere_permiso('discrepancias.ver')
def edicion(request, edicion_id):
    """Verificación de una edición: hallazgos automáticos, discrepancias y confirmaciones."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    hallazgos = verificar_edicion(edicion)
    return render(
        request,
        'auditoria/edicion.html',
        {
            'edicion': edicion,
            'hallazgos': hallazgos,
            'votaciones': resumen_votaciones(edicion),
            'discrepancias': edicion.discrepancias.select_related(
                'votacion', 'reportada_por', 'resuelta_por'
            ),
            'confirmaciones': edicion.confirmaciones.select_related('auditor', 'votacion'),
            'tipos': Discrepancia.TIPOS,
            'puede_verificar': flujo.puede_verificar(request.user),
            'responsable': flujo.responsable_actual(),
        },
    )


@require_POST
@requiere_permiso('discrepancias.reportar')
def reportar(request, edicion_id):
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    votacion = None
    votacion_id = request.POST.get('votacion') or ''
    if votacion_id.isdigit():
        votacion = get_object_or_404(Votacion, pk=votacion_id, edicion=edicion)
    try:
        discrepancia = flujo.reportar(
            request,
            edicion,
            tipo=request.POST.get('tipo', ''),
            descripcion=request.POST.get('descripcion', ''),
            votacion=votacion,
            evidencia={'origen': request.POST.get('origen', 'manual')},
        )
    except flujo.AccionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            f'Discrepancia registrada. La resuelve: {flujo.responsable_actual()}.',
        )
        return redirect('auditoria_discrepancia', discrepancia_id=discrepancia.pk)
    return redirect('auditoria_edicion', edicion_id=edicion.pk)


@require_POST
@requiere_permiso('discrepancias.reportar')
def confirmar_edicion(request, edicion_id):
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    try:
        flujo.confirmar_en_orden(request, edicion, request.POST.get('observacion', ''))
    except flujo.AccionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            f'Quedó constancia de que «{edicion}» está en orden '
            f'({edicion.get_estado_display().lower()}).',
        )
    return redirect('auditoria_edicion', edicion_id=edicion.pk)


@requiere_permiso('discrepancias.ver')
def discrepancia_lista(request):
    """Bandeja de discrepancias, por defecto las abiertas."""
    filtro = request.GET.get('estado', Discrepancia.ABIERTA)
    lista = Discrepancia.objects.select_related('edicion', 'votacion', 'reportada_por')
    if filtro in dict(Discrepancia.ESTADOS):
        lista = lista.filter(estado=filtro)
    return render(
        request,
        'auditoria/discrepancia_lista.html',
        {
            'discrepancias': lista,
            'filtro': filtro,
            'estados': Discrepancia.ESTADOS,
            'responsable': flujo.responsable_actual(),
            'puede_resolver': flujo.puede_resolver(request.user),
        },
    )


@requiere_permiso('discrepancias.ver')
def discrepancia_detalle(request, discrepancia_id):
    discrepancia = get_object_or_404(
        Discrepancia.objects.select_related(
            'edicion', 'votacion', 'reportada_por', 'resuelta_por', 'confirmada_por'
        ),
        pk=discrepancia_id,
    )
    return render(
        request,
        'auditoria/discrepancia_detalle.html',
        {
            'discrepancia': discrepancia,
            'responsable': flujo.responsable_actual(),
            'puede_resolver': flujo.puede_resolver(request.user),
            'puede_verificar': flujo.puede_verificar(request.user),
        },
    )


@require_POST
@requiere_permiso('discrepancias.ver')
def discrepancia_accion(request, discrepancia_id, accion):
    """resolver | descartar (organizador/administrador) · confirmar | reabrir (auditor)."""
    discrepancia = get_object_or_404(Discrepancia, pk=discrepancia_id)
    # Cada acción exige su propio permiso: resolver es de quien resuelve,
    # confirmar o reabrir es del auditor.
    if accion in ('resolver', 'descartar') and not flujo.puede_resolver(request.user):
        return sin_permiso(request, 'discrepancias.resolver')
    if accion in ('confirmar', 'reabrir') and not flujo.puede_verificar(request.user):
        return sin_permiso(request, 'discrepancias.reportar')
    texto = request.POST.get('texto', '')
    mensajes = {
        'resolver': 'Discrepancia resuelta. El auditor puede confirmar la resolución.',
        'descartar': 'Discrepancia descartada. El auditor puede confirmarlo o reabrirla.',
        'confirmar': 'Resolución confirmada por el auditor.',
        'reabrir': 'Discrepancia reabierta.',
    }
    try:
        if accion == 'resolver':
            flujo.resolver(request, discrepancia, texto)
        elif accion == 'descartar':
            flujo.resolver(request, discrepancia, texto, descartar=True)
        elif accion == 'confirmar':
            flujo.confirmar_resolucion(request, discrepancia)
        elif accion == 'reabrir':
            flujo.reabrir(request, discrepancia, texto)
        else:
            messages.error(request, 'Acción desconocida.')
            return redirect('auditoria_discrepancia', discrepancia_id=discrepancia.pk)
    except flujo.AccionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(request, mensajes[accion])
    return redirect('auditoria_discrepancia', discrepancia_id=discrepancia.pk)
