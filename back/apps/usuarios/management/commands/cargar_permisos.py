"""Carga el catálogo de permisos y los asigna a los roles (entregable P2)."""

from django.core.management.base import BaseCommand
from django.db import transaction

from back.apps.usuarios.models import Permission, Role, RolPermiso
from back.apps.usuarios.permisos import PERMISOS_POR_ROL, codigos_del_catalogo


class Command(BaseCommand):
    help = (
        'Crea el catálogo de permisos (ediciones.*, categorias.*, votaciones.*, '
        'opciones.*, usuarios.*, resultados.ver, padron.ver, auditoria.ver) y los '
        'asigna a los cuatro roles. Es idempotente: ejecutarlo dos veces no '
        'duplica nada.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        creados = 0

        for modulo, definiciones in {
            'ediciones': None, 'categorias': None, 'votaciones': None,
            'opciones': None, 'usuarios': None,
        }.items():
            for nombre in ('ver', 'crear', 'editar', 'eliminar'):
                _, created = Permission.objects.get_or_create(
                    codigo=f'{modulo}.{nombre}',
                    defaults={
                        'modulo': modulo,
                        'descripcion': f'{nombre.capitalize()} {modulo}',
                    },
                )
                creados += created

        for codigo in ('resultados.ver', 'padron.ver', 'auditoria.ver'):
            _, created = Permission.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'modulo': codigo.split('.')[0],
                    'descripcion': 'Consultar ' + codigo.split('.')[0],
                },
            )
            creados += created

        asignados = 0
        for nombre_rol, codigos in PERMISOS_POR_ROL.items():
            rol, _ = Role.objects.get_or_create(nombre=nombre_rol)
            for codigo in codigos:
                permiso = Permission.objects.get(codigo=codigo)
                _, created = RolPermiso.objects.get_or_create(
                    rol=rol, permiso=permiso
                )
                asignados += created

        self.stdout.write(self.style.SUCCESS(
            f'Permisos listos: {creados} códigos nuevos del catálogo, '
            f'{asignados} asignaciones nuevas. '
            f'Total de códigos del catálogo: {len(codigos_del_catalogo())}.'
        ))
