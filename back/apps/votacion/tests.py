from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from back.apps.elecciones.models import (
    Categoria,
    Edicion,
    Opcion,
    OpcionVotacion,
    Votacion,
)


class OpcionesVotacionEndpointTests(APITestCase):

    def setUp(self):
        ahora = timezone.now()

        self.edicion = Edicion.objects.create(
            nombre='Elecciones de prueba',
            anio=2026,
            estado='ACTIVA',
        )

        self.categoria = Categoria.objects.create(nombre='Rey Vallenato')

        self.votacion = Votacion.objects.create(
            edicion=self.edicion,
            categoria=self.categoria,
            fecha_apertura=ahora,
            fecha_cierre=ahora + timedelta(days=1),
            estado='ACTIVA',
        )

        self.otra_votacion = Votacion.objects.create(
            edicion=self.edicion,
            categoria=Categoria.objects.create(nombre='Canción Inédita'),
            fecha_apertura=ahora,
            fecha_cierre=ahora + timedelta(days=1),
            estado='ACTIVA',
        )

        self.opcion = Opcion.objects.create(
            nombre='Candidato de prueba',
            identificador_unico='candidato-prueba',
            biografia='Registro utilizado únicamente para pruebas',
        )

        self.opcion_votacion = OpcionVotacion.objects.create(
            votacion=self.votacion,
            opcion=self.opcion,
            numero_casilla=1,
            es_voto_blanco=False,
            partido_lista='Lista de prueba',
        )

        OpcionVotacion.objects.create(
            votacion=self.otra_votacion,
            opcion=Opcion.objects.create(
                nombre='Candidato de otra categoría',
                identificador_unico='candidato-otra-categoria',
            ),
            numero_casilla=1,
            es_voto_blanco=False,
        )

    def test_ruta_opciones_esta_registrada(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'votacion_id': self.votacion.id}
        )

        self.assertEqual(
            url,
            f'/api/votacion/votaciones/{self.votacion.id}/opciones/'
        )

    def test_consulta_opciones_responde_correctamente(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'votacion_id': self.votacion.id}
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_consulta_devuelve_solo_opciones_de_su_votacion(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'votacion_id': self.votacion.id}
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(
            respuesta.data[0]['opcion_detalle']['nombre'],
            'Candidato de prueba'
        )

    def test_consulta_incluye_numero_de_casilla(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'votacion_id': self.votacion.id}
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.data[0]['numero_casilla'], 1)
        self.assertEqual(respuesta.data[0]['partido_lista'], 'Lista de prueba')
