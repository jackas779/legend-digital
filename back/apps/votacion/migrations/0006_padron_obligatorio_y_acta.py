"""Padrón siempre con edición y categoría; acta sin PDF obligatorio.

Con ``edicion`` o ``categoria`` en NULL la constraint
``uq_usuario_categoria_edicion`` no aplica (en SQL dos NULL no son
iguales), así que la regla de un voto por categoría quedaba sin efecto en
esas filas. Primero se completan desde la votación y luego se vuelven
obligatorias.
"""

import django.db.models.deletion
from django.db import migrations, models


def completar_padron(apps, schema_editor):
    PadronVotante = apps.get_model('votacion', 'PadronVotante')
    pendientes = PadronVotante.objects.filter(
        models.Q(edicion__isnull=True) | models.Q(categoria__isnull=True)
    ).select_related('votacion')
    for padron in pendientes:
        padron.edicion_id = padron.votacion.edicion_id
        padron.categoria_id = padron.votacion.categoria_id
        padron.save(update_fields=['edicion', 'categoria'])


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0005_ciclo_de_vida_edicion'),
        ('votacion', '0005_padronvotante_categoria_padronvotante_edicion_and_more'),
    ]

    operations = [
        migrations.RunPython(completar_padron, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='padronvotante',
            name='edicion',
            field=models.ForeignKey(
                help_text='Copia desnormalizada de la edición de la votación.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='padrones',
                to='elecciones.edicion',
            ),
        ),
        migrations.AlterField(
            model_name='padronvotante',
            name='categoria',
            field=models.ForeignKey(
                help_text='Copia desnormalizada de la categoría de la votación.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='padrones',
                to='elecciones.categoria',
            ),
        ),
        migrations.AlterField(
            model_name='actaescrutinio',
            name='archivo_pdf_url',
            field=models.URLField(blank=True, default=''),
        ),
    ]
