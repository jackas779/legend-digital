# Modelo MVP: Edición → Categoría → Votación → Opción → Voto.
# La opción deja de ser un catálogo global y pasa a pertenecer a una votación.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0003_modelo_electoral_normalizado'),
        # VotoUrna referenciaba OpcionVotacion: debe desaparecer antes de borrarla.
        ('votacion', '0004_urna_simplificada'),
    ]

    operations = [
        # --- Votación ahora tiene nombre propio ---
        migrations.AddField(
            model_name='votacion',
            name='nombre',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AlterField(
            model_name='votacion',
            name='nombre',
            field=models.CharField(max_length=150),
        ),
        migrations.AddField(
            model_name='votacion',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name='votacion',
            constraint=models.UniqueConstraint(
                fields=('edicion', 'categoria', 'nombre'),
                name='uq_votacion_titulo',
            ),
        ),
        migrations.AddConstraint(
            model_name='edicion',
            constraint=models.UniqueConstraint(
                fields=('nombre', 'anio'),
                name='uq_edicion_nombre_anio',
            ),
        ),

        # --- La tabla puente desaparece: la opción cuelga de la votación ---
        migrations.DeleteModel(name='OpcionVotacion'),

        migrations.RemoveField(model_name='opcion', name='identificador_unico'),
        migrations.RemoveField(model_name='opcion', name='biografia'),
        migrations.AddField(
            model_name='opcion',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='opcion',
            name='subtitulo',
            field=models.CharField(
                blank=True,
                help_text='Artista, lista o partido que acompaña a la opción.',
                max_length=150,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='opcion',
            name='orden',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Número de casilla en el tarjetón.',
            ),
        ),
        migrations.AlterField(
            model_name='opcion',
            name='orden',
            field=models.PositiveIntegerField(
                help_text='Número de casilla en el tarjetón.',
            ),
        ),
        migrations.AddField(
            model_name='opcion',
            name='es_voto_blanco',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='opcion',
            name='votacion',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='opciones',
                to='elecciones.votacion',
            ),
        ),
        migrations.AlterField(
            model_name='opcion',
            name='votacion',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='opciones',
                to='elecciones.votacion',
            ),
        ),
        migrations.AlterModelOptions(
            name='opcion',
            options={
                'ordering': ['orden', 'nombre'],
                'verbose_name': 'opción',
                'verbose_name_plural': 'opciones',
            },
        ),
        migrations.AddConstraint(
            model_name='opcion',
            constraint=models.UniqueConstraint(
                fields=('votacion', 'orden'),
                name='uq_votacion_casilla',
            ),
        ),
    ]
