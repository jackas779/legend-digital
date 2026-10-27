"""Pantalla web del registro de auditoría (rol Auditor / Administrador)."""

from django.shortcuts import render

from back.apps.usuarios.permisos import requiere_permiso

from .models import LogAuditoriaEvento


@requiere_permiso('auditoria.ver')
def lista(request):
    """Últimos eventos del sistema, del más reciente al más antiguo."""
    eventos = (
        LogAuditoriaEvento.objects
        .select_related('usuario')
        .order_by('-id')[:150]
    )
    return render(request, 'auditoria/log_lista.html', {'eventos': eventos})
