
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from back.apps.elecciones.models import (
    CategoriaElectoral,
    CandidatoOpcion,
)


class OpcionesVotacionEndpointTests(APITestCase):

    def setUp(self):
        ahora = timezone.now()

        self.categoria = CategoriaElectoral.objects.create(
            titulo='Rey Vallenato - Prueba',
            descripcion='Categoría utilizada para pruebas automatizadas',
            fecha_apertura=ahora,
            fecha_cierre=ahora + timedelta(days=1),
            estado='ACTIVA',
        )

        self.otra_categoria = CategoriaElectoral.objects.create(
            titulo='Canción Inédita - Prueba',
            descripcion='Segunda categoría de prueba',
            fecha_apertura=ahora,
            fecha_cierre=ahora + timedelta(days=1),
            estado='ACTIVA',
        )

        self.opcion = CandidatoOpcion.objects.create(
            categoria=self.categoria,
            nombre_candidato='Candidato de prueba',
            partido_lista='Lista de prueba',
            biografia='Registro utilizado únicamente para pruebas',
            orden_casilla=1,
            es_voto_blanco=False,
        )

        CandidatoOpcion.objects.create(
            categoria=self.otra_categoria,
            nombre_candidato='Candidato de otra categoría',
            partido_lista='Otra lista',
            orden_casilla=1,
            es_voto_blanco=False,
        )

    def test_ruta_opciones_esta_registrada(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'categoria_id': self.categoria.id}
        )

        self.assertEqual(
            url,
            f'/api/votacion/categorias/{self.categoria.id}/opciones/'
        )

    def test_consulta_opciones_responde_correctamente(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'categoria_id': self.categoria.id}
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_consulta_devuelve_solo_opciones_de_su_categoria(self):
        url = reverse(
            'votacion-opciones',
            kwargs={'categoria_id': self.categoria.id}
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(
            respuesta.data[0]['nombre_candidato'],
            'Candidato de prueba'
        )
