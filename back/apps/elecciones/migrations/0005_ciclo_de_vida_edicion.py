"""Ciclo de vida de la edición y estados propios de la votación.

- Edición: periodo (fecha_inicio/fecha_fin) y datos de cierre anticipado.
- Votación: deja de compartir los estados de la edición y pasa a los suyos
  (BORRADOR, LISTA, ABIERTA, CERRADA, ESCRUTADA, CANCELADA).
- Categoría: puede archivarse.

Los datos existentes se trasladan así:

- Periodo de la edición = primera apertura → último cierre de sus votaciones.
- Votación: BORRADOR → BORRADOR, PROGRAMADA → LISTA, ACTIVA → ABIERTA,
  CERRANDO/FINALIZADA → CERRADA.
- Si la edición ya estaba FINALIZADA o CERRANDO, ninguna votación queda
  viva: las que se abrieron pasan a CERRADA y las que nunca se abrieron a
  CANCELADA (regla de cierre en cascada).
- Una votación CERRADA que ya tiene acta queda ESCRUTADA.
"""

from django.db import migrations, models
from django.db.models import Max, Min

MAPEO_VOTACION = {
    'BORRADOR': 'BORRADOR',
    'PROGRAMADA': 'LISTA',
    'ACTIVA': 'ABIERTA',
    'CERRANDO': 'CERRADA',
    'FINALIZADA': 'CERRADA',
}


def trasladar(apps, schema_editor):
    Edicion = apps.get_model('elecciones', 'Edicion')
    Votacion = apps.get_model('elecciones', 'Votacion')

    for anterior, nuevo in MAPEO_VOTACION.items():
        Votacion.objects.filter(estado=anterior).update(estado=nuevo)

    for edicion in Edicion.objects.all():
        rango = Votacion.objects.filter(edicion=edicion).aggregate(
            inicio=Min('fecha_apertura'), fin=Max('fecha_cierre')
        )
        edicion.fecha_inicio = rango['inicio']
        edicion.fecha_fin = rango['fin']
        edicion.save(update_fields=['fecha_inicio', 'fecha_fin'])

        if edicion.estado in ('CERRANDO', 'FINALIZADA'):
            Votacion.objects.filter(edicion=edicion, estado='ABIERTA').update(estado='CERRADA')
            Votacion.objects.filter(
                edicion=edicion, estado__in=('BORRADOR', 'LISTA')
            ).update(estado='CANCELADA')

    # Las votaciones cerradas que ya tienen acta están escrutadas.
    ActaEscrutinio = apps.get_model('votacion', 'ActaEscrutinio')
    con_acta = ActaEscrutinio.objects.values_list('votacion_id', flat=True)
    Votacion.objects.filter(estado='CERRADA', pk__in=list(con_acta)).update(estado='ESCRUTADA')


def revertir(apps, schema_editor):
    Votacion = apps.get_model('elecciones', 'Votacion')
    inverso = {
        'BORRADOR': 'BORRADOR',
        'LISTA': 'PROGRAMADA',
        'ABIERTA': 'ACTIVA',
        'CERRADA': 'FINALIZADA',
        'ESCRUTADA': 'FINALIZADA',
        'CANCELADA': 'FINALIZADA',
    }
    for actual, anterior in inverso.items():
        Votacion.objects.filter(estado=actual).update(estado=anterior)


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0004_modelo_mvp'),
        # Para leer las actas existentes (ActaEscrutinio) en el traslado.
        ('votacion', '0005_padronvotante_categoria_padronvotante_edicion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='edicion',
            name='fecha_inicio',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Al llegar esta fecha una edición PROGRAMADA se activa sola.',
            ),
        ),
        migrations.AddField(
            model_name='edicion',
            name='fecha_fin',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Al llegar esta fecha la edición se cierra sola.',
            ),
        ),
        migrations.AddField(
            model_name='edicion',
            name='cierre_anticipado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='edicion',
            name='motivo_cierre',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='edicion',
            name='fecha_cierre_real',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edicion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('BORRADOR', 'Borrador'),
                    ('PROGRAMADA', 'Programada'),
                    ('ACTIVA', 'Activa'),
                    ('CERRANDO', 'En escrutinio'),
                    ('FINALIZADA', 'Finalizada'),
                ],
                default='BORRADOR',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='categoria',
            name='archivada',
            field=models.BooleanField(
                default=False,
                help_text='Archivada: no se ofrece a ediciones nuevas, pero se conserva su historial.',
            ),
        ),
        migrations.AlterField(
            model_name='votacion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('BORRADOR', 'Borrador'),
                    ('LISTA', 'Lista'),
                    ('ABIERTA', 'Abierta'),
                    ('CERRADA', 'Cerrada'),
                    ('ESCRUTADA', 'Escrutada'),
                    ('CANCELADA', 'Cancelada'),
                ],
                default='BORRADOR',
                max_length=20,
            ),
        ),
        migrations.RunPython(trasladar, revertir),
    ]
