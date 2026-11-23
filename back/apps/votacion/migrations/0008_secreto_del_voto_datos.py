"""Secreto del voto sobre los datos existentes.

Antes, el comprobante del padrón era la misma firma del voto (cruzando
ambas tablas se sabía quién votó qué) y el voto guardaba la hora exacta
(cruzable con la hora en que votó cada persona). Aquí:

1. Cada comprobante se reemplaza por un código aleatorio.
2. La hora de cada voto se redondea a la hora y su firma se recalcula.
3. El sello de cada acta se recalcula, porque depende de las firmas.

Es irreversible a propósito: volver atrás reabriría el cruce.
"""

import hashlib
import secrets

from django.db import migrations


def firma(voto):
    contenido = f'{voto.id}:{voto.opcion_id}:{voto.fecha_registro.isoformat()}'
    return hashlib.sha256(contenido.encode('utf-8')).hexdigest()


def proteger(apps, schema_editor):
    PadronVotante = apps.get_model('votacion', 'PadronVotante')
    Voto = apps.get_model('votacion', 'Voto')
    ActaEscrutinio = apps.get_model('votacion', 'ActaEscrutinio')

    for padron in PadronVotante.objects.exclude(hash_comprobante__isnull=True).only('pk'):
        PadronVotante.objects.filter(pk=padron.pk).update(hash_comprobante=secrets.token_hex(32))

    for voto in Voto.objects.all().only('id', 'opcion_id', 'fecha_registro'):
        voto.fecha_registro = voto.fecha_registro.replace(minute=0, second=0, microsecond=0)
        Voto.objects.filter(pk=voto.pk).update(
            fecha_registro=voto.fecha_registro, firma_criptografica=firma(voto)
        )

    for acta in ActaEscrutinio.objects.all():
        firmas = sorted(
            Voto.objects.filter(opcion__votacion_id=acta.votacion_id)
            .values_list('firma_criptografica', flat=True)
        )
        contenido = f'{acta.votacion_id}|{len(firmas)}|' + '|'.join(firmas)
        acta.hash_sello_bd = hashlib.sha256(contenido.encode('utf-8')).hexdigest()
        acta.save(update_fields=['hash_sello_bd'])


class Migration(migrations.Migration):

    dependencies = [
        ('votacion', '0007_secreto_rondas_e_inscripciones'),
    ]

    operations = [
        migrations.RunPython(proteger, migrations.RunPython.noop),
    ]
