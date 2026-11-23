"""Carga el catálogo de permisos y los asigna a los roles (entregable P2)."""

from django.core.management.base import BaseCommand

from back.apps.usuarios.permisos import codigos_del_catalogo, sincronizar_catalogo


class Command(BaseCommand):
    help = (
        'Crea el catálogo de permisos y los asigna a los cuatro roles (los crea '
        'si faltan). Es idempotente: ejecutarlo dos veces no duplica nada. '
        '"migrate" ya lo sincroniza solo para los roles existentes.'
    )

    def handle(self, *args, **options):
        creados, asignados = sincronizar_catalogo(crear_roles=True)
        self.stdout.write(self.style.SUCCESS(
            f'Permisos listos: {creados} códigos nuevos del catálogo, '
            f'{asignados} asignaciones nuevas. '
            f'Total de códigos del catálogo: {len(codigos_del_catalogo())}.'
        ))
