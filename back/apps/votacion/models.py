from django.conf import settings
from django.db import models

from back.apps.elecciones.models import CategoriaElectoral, CandidatoOpcion
from back.apps.usuarios.models import Usuario


class ParticipacionVotante(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='participaciones')
    categoria = models.ForeignKey(CategoriaElectoral, on_delete=models.CASCADE, related_name='participantes')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    hash_comprobante = models.CharField(max_length=256, unique=True)

    class Meta:
        db_table = 'participacion_votantes'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'categoria'], name='uq_usuario_categoria')
        ]

    def __str__(self):
        return f'{self.usuario} -> {self.categoria}'


class UrnaDigitalVoto(models.Model):
    categoria = models.ForeignKey(CategoriaElectoral, on_delete=models.CASCADE, related_name='votos_urna')
    candidato = models.ForeignKey(CandidatoOpcion, on_delete=models.CASCADE, related_name='votos_urna')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    firma_criptografica = models.CharField(max_length=256)

    class Meta:
        db_table = 'urna_digital_votos'

    def __str__(self):
        return f'Voto en {self.categoria}'


class CertificadoVotacion(models.Model):
    participacion = models.OneToOneField(ParticipacionVotante, on_delete=models.CASCADE, related_name='certificado')
    codigo_certificado = models.CharField(max_length=100, unique=True)
    qr_verificacion_url = models.TextField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'certificados_votacion'

    def __str__(self):
        return self.codigo_certificado


class ActaEscrutinio(models.Model):
    categoria = models.OneToOneField(CategoriaElectoral, on_delete=models.CASCADE, related_name='acta')
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    total_padron_habilitado = models.IntegerField()
    total_participantes = models.IntegerField()
    total_votos_urna = models.IntegerField()
    archivo_pdf_url = models.URLField()
    hash_sello_bd = models.CharField(max_length=256)

    class Meta:
        db_table = 'actas_escrutinio'

    def __str__(self):
        return f'Acta {self.categoria}'
