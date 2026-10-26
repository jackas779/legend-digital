# Urna digital, padrón y certificados con el modelo normalizado.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('votacion', '0002_eliminar_modelos_anteriores'),
        ('elecciones', '0003_modelo_electoral_normalizado'),
    ]

    operations = [
        migrations.CreateModel(
            name='PadronVotante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ha_votado', models.BooleanField(default=False)),
                ('fecha_emision', models.DateTimeField(auto_now_add=True)),
                ('hash_comprobante', models.CharField(blank=True, max_length=256, null=True, unique=True)),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='padrones',
                    to='usuarios.usuario',
                )),
                ('votacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='padron',
                    to='elecciones.votacion',
                )),
            ],
            options={
                'verbose_name': 'padrón de votante',
                'verbose_name_plural': 'padrón de votantes',
                'db_table': 'padron_votantes',
            },
        ),
        migrations.CreateModel(
            name='CertificadoVotacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_certificado', models.CharField(max_length=100, unique=True)),
                ('qr_verificacion_url', models.TextField()),
                ('fecha_generacion', models.DateTimeField(auto_now_add=True)),
                ('padron', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='certificado',
                    to='votacion.padronvotante',
                )),
            ],
            options={
                'verbose_name': 'certificado de votación',
                'verbose_name_plural': 'certificados de votación',
                'db_table': 'certificados_votacion',
            },
        ),
        migrations.CreateModel(
            name='VotoUrna',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('firma_criptografica', models.CharField(max_length=256)),
                ('opcion_votacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votos_urna',
                    to='elecciones.opcionvotacion',
                )),
                ('votacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votos_urna',
                    to='elecciones.votacion',
                )),
            ],
            options={
                'verbose_name': 'voto en urna',
                'verbose_name_plural': 'votos en urna',
                'db_table': 'votos_urna',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.CreateModel(
            name='ActaEscrutinio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_cierre', models.DateTimeField(auto_now_add=True)),
                ('total_padron_habilitado', models.PositiveIntegerField()),
                ('total_participantes', models.PositiveIntegerField()),
                ('total_votos_urna', models.PositiveIntegerField()),
                ('archivo_pdf_url', models.URLField()),
                ('hash_sello_bd', models.CharField(max_length=256)),
                ('votacion', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='acta',
                    to='elecciones.votacion',
                )),
            ],
            options={
                'verbose_name': 'acta de escrutinio',
                'verbose_name_plural': 'actas de escrutinio',
                'db_table': 'actas_escrutinio',
            },
        ),
        migrations.AddConstraint(
            model_name='padronvotante',
            constraint=models.UniqueConstraint(
                fields=('usuario', 'votacion'),
                name='uq_usuario_votacion',
            ),
        ),
    ]
