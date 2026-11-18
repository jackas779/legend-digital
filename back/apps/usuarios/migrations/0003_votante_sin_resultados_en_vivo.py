"""El votante deja de ver resultados antes del cierre.

Ver cómo va cada opción mientras la votación está abierta puede influir en
quien todavía no vota. ``resultados.ver`` (resultados en vivo) queda para
el organizador, el auditor y el administrador; el votante ve los
resultados cuando la votación cierra. ``cargar_permisos`` solo agrega
asignaciones, por eso la de las bases existentes se quita aquí.
"""

from django.db import migrations


def quitar(apps, schema_editor):
    RolPermiso = apps.get_model('usuarios', 'RolPermiso')
    RolPermiso.objects.filter(
        rol__nombre='Votante', permiso__codigo='resultados.ver'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_rolpermiso'),
    ]

    operations = [
        migrations.RunPython(quitar, migrations.RunPython.noop),
    ]
