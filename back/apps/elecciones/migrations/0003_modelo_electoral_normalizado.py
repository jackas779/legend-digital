# Migración del modelo electoral plano al modelo normalizado:
# Edición → Votación → Categoría, Opción / OpciónVotación.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0002_alter_categoriaelectoral_creador'),
        ('usuarios', '0002_rolpermiso'),
        # Primero deben desaparecer las tablas de votación que referencian
        # al esquema anterior (categorías y candidatos).
        ('votacion', '0002_eliminar_modelos_anteriores'),
    ]

    operations = [
        # ---------- Eliminar el esquema anterior ----------
        migrations.DeleteModel(name='CandidatoOpcion'),
        migrations.DeleteModel(name='Normativa'),
        migrations.DeleteModel(name='CategoriaElectoral'),
        migrations.DeleteModel(name='RecursoMultimedia'),

        # ---------- Módulo 2: jerarquía electoral normalizada ----------
        migrations.CreateModel(
            name='Edicion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('anio', models.PositiveIntegerField()),
                ('estado', models.CharField(
                    choices=[
                        ('BORRADOR', 'Borrador'),
                        ('PROGRAMADA', 'Programada'),
                        ('ACTIVA', 'Activa'),
                        ('CERRANDO', 'Cerrando'),
                        ('FINALIZADA', 'Finalizada'),
                    ],
                    default='BORRADOR',
                    max_length=20,
                )),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('creador', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='ediciones_gestionadas',
                    to='usuarios.usuario',
                )),
            ],
            options={
                'verbose_name': 'edición',
                'verbose_name_plural': 'ediciones',
                'db_table': 'ediciones',
                'ordering': ['-anio', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150, unique=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'categoría',
                'verbose_name_plural': 'categorías',
                'db_table': 'categorias',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='RecursoMultimedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_archivo', models.CharField(max_length=150)),
                ('url_publica', models.URLField()),
                ('tipo_mime', models.CharField(max_length=50)),
                ('peso_bytes', models.PositiveIntegerField()),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'recursos_multimedia',
                'ordering': ['-fecha_subida'],
            },
        ),
        migrations.CreateModel(
            name='Votacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_apertura', models.DateTimeField()),
                ('fecha_cierre', models.DateTimeField()),
                ('estado', models.CharField(
                    choices=[
                        ('BORRADOR', 'Borrador'),
                        ('PROGRAMADA', 'Programada'),
                        ('ACTIVA', 'Activa'),
                        ('CERRANDO', 'Cerrando'),
                        ('FINALIZADA', 'Finalizada'),
                    ],
                    default='BORRADOR',
                    max_length=20,
                )),
                ('mostrar_resultados_en_vivo', models.BooleanField(default=False)),
                ('categoria', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='votaciones',
                    to='elecciones.categoria',
                )),
                ('edicion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votaciones',
                    to='elecciones.edicion',
                )),
            ],
            options={
                'verbose_name': 'votación',
                'verbose_name_plural': 'votaciones',
                'db_table': 'votaciones',
                'ordering': ['-fecha_apertura'],
            },
        ),
        migrations.CreateModel(
            name='Opcion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('identificador_unico', models.CharField(max_length=100, unique=True)),
                ('biografia', models.TextField(blank=True, null=True)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('foto_recurso', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='opciones',
                    to='elecciones.recursomultimedia',
                )),
            ],
            options={
                'verbose_name': 'opción',
                'verbose_name_plural': 'opciones',
                'db_table': 'opciones',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='OpcionVotacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_casilla', models.PositiveIntegerField()),
                ('es_voto_blanco', models.BooleanField(default=False)),
                ('partido_lista', models.CharField(blank=True, max_length=120, null=True)),
                ('opcion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='participaciones',
                    to='elecciones.opcion',
                )),
                ('votacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='opciones',
                    to='elecciones.votacion',
                )),
            ],
            options={
                'verbose_name': 'opción de votación',
                'verbose_name_plural': 'opciones de votación',
                'db_table': 'opciones_votacion',
                'ordering': ['numero_casilla'],
            },
        ),
        migrations.CreateModel(
            name='Normativa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=150)),
                ('contenido_html', models.TextField(blank=True, null=True)),
                ('archivo_pdf_url', models.URLField(blank=True, null=True)),
                ('fecha_publicacion', models.DateTimeField(auto_now_add=True)),
                ('votacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='normativas',
                    to='elecciones.votacion',
                )),
            ],
            options={
                'db_table': 'normativas',
                'ordering': ['-fecha_publicacion'],
            },
        ),
        migrations.AddConstraint(
            model_name='opcionvotacion',
            constraint=models.UniqueConstraint(
                fields=('votacion', 'numero_casilla'),
                name='uq_votacion_casilla',
            ),
        ),
        migrations.AddConstraint(
            model_name='opcionvotacion',
            constraint=models.UniqueConstraint(
                fields=('votacion', 'opcion'),
                name='uq_votacion_opcion',
            ),
        ),
    ]
