"""Pantalla web del registro de auditoría (rol Auditor / Administrador).

El auditor audita el proceso y los votos, no a las personas: ve lo que
hace el equipo de gestión (programar, cerrar, escrutar, editar…) y los
intentos fallidos de inicio de sesión como alerta de seguridad, pero no
la actividad de cada votante (sus ingresos, inscripciones o votos). Los
votos emitidos aparecen sin identidad. El administrador ve el registro
completo.
"""

from django.db.models import Q
from django.shortcuts import render

from back.apps.usuarios.permisos import requiere_permiso

from .models import LogAuditoriaEvento


def _es_administrador(user):
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil_usuario', None)
    return getattr(getattr(perfil, 'rol', None), 'nombre', None) == 'Administrador'


@requiere_permiso('auditoria.ver')
def lista(request):
    """Últimos eventos del sistema, del más reciente al más antiguo."""
    eventos = LogAuditoriaEvento.objects.select_related('usuario')
    if not _es_administrador(request.user):
        eventos = eventos.exclude(
            Q(usuario__perfil_usuario__rol__nombre='Votante')
            & ~Q(accion='login_fallido')
        )
    return render(
        request,
        'auditoria/log_lista.html',
        {
            'eventos': eventos.order_by('-id')[:150],
            'vista_auditor': not _es_administrador(request.user),
        },
    )
