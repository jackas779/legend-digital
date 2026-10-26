from django.db import migrations


class Migration(migrations.Migration):
    """Elimina las tablas antiguas antes de normalizar elecciones.

    La base de desarrollo no contiene votos ni participaciones, por lo que
    se pueden recrear las tablas con el nuevo esquema sin pérdida de datos.
    """

    dependencies = [
        ('votacion', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='CertificadoVotacion'),
        migrations.DeleteModel(name='UrnaDigitalVoto'),
        migrations.DeleteModel(name='ParticipacionVotante'),
        migrations.DeleteModel(name='ActaEscrutinio'),
    ]
