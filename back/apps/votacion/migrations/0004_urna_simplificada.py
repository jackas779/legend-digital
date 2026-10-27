# Urna simplificada: el voto apunta directo a la opción y el padrón usa auth.User.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('votacion', '0003_modelo_normalizado'),
        ('elecciones', '0003_modelo_electoral_normalizado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # El voto deja de referenciar la tabla puente opciones_votacion.
        migrations.DeleteModel(name='VotoUrna'),
        migrations.CreateModel(
            name='Voto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('firma_criptografica', models.CharField(blank=True, default='', max_length=256)),
                ('opcion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votos',
                    to='elecciones.opcion',
                )),
            ],
            options={
                'verbose_name': 'voto',
                'verbose_name_plural': 'votos',
                'db_table': 'votos',
                'ordering': ['-fecha_registro'],
            },
        ),
        # El padrón se apoya en auth.User para que cualquier usuario de Django
        # pueda votar sin necesitar un perfil con rol.
        migrations.AlterField(
            model_name='padronvotante',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='padrones',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
