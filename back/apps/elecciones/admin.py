from django.contrib import admin

from back.apps.usuarios.permisos import AdminPermisosMixin

from .models import Categoria, Edicion, Normativa, Opcion, RecursoMultimedia, Votacion


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1
    fields = ('orden', 'nombre', 'subtitulo', 'es_voto_blanco')
    ordering = ('orden',)


class NormativaInline(admin.TabularInline):
    model = Normativa
    extra = 0
    fields = ('titulo', 'archivo_pdf_url')


class VotacionInline(admin.TabularInline):
    model = Votacion
    extra = 0
    fields = ('nombre', 'categoria', 'estado', 'fecha_apertura', 'fecha_cierre')


@admin.register(Edicion)
class EdicionAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'ediciones.ver'
    codigo_crear = 'ediciones.crear'
    codigo_editar = 'ediciones.editar'
    codigo_eliminar = 'ediciones.eliminar'
    list_display = ('nombre', 'anio', 'estado', 'creador', 'fecha_creacion')
    list_filter = ('estado', 'anio')
    search_fields = ('nombre',)
    inlines = [VotacionInline]


@admin.register(Categoria)
class CategoriaAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'categorias.ver'
    codigo_crear = 'categorias.crear'
    codigo_editar = 'categorias.editar'
    codigo_eliminar = 'categorias.eliminar'
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Votacion)
class VotacionAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'votaciones.ver'
    codigo_crear = 'votaciones.crear'
    codigo_editar = 'votaciones.editar'
    codigo_eliminar = 'votaciones.eliminar'
    list_display = (
        'nombre',
        'categoria',
        'edicion',
        'estado',
        'fecha_apertura',
        'fecha_cierre',
        'total_votos',
    )
    list_filter = ('estado', 'edicion', 'categoria')
    search_fields = ('nombre',)
    inlines = [OpcionInline, NormativaInline]


@admin.register(Opcion)
class OpcionAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'opciones.ver'
    codigo_crear = 'opciones.crear'
    codigo_editar = 'opciones.editar'
    codigo_eliminar = 'opciones.eliminar'
    list_display = ('orden', 'nombre', 'subtitulo', 'votacion', 'es_voto_blanco')
    list_filter = ('votacion__edicion', 'votacion', 'es_voto_blanco')
    search_fields = ('nombre', 'subtitulo')
    ordering = ('votacion', 'orden')


@admin.register(Normativa)
class NormativaAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'votaciones.ver'
    codigo_crear = 'votaciones.editar'
    codigo_editar = 'votaciones.editar'
    codigo_eliminar = 'votaciones.eliminar'
    list_display = ('titulo', 'votacion', 'fecha_publicacion')
    list_filter = ('votacion',)
    search_fields = ('titulo',)


@admin.register(RecursoMultimedia)
class RecursoMultimediaAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'votaciones.ver'
    codigo_crear = 'votaciones.editar'
    codigo_editar = 'votaciones.editar'
    codigo_eliminar = 'votaciones.eliminar'
    list_display = ('nombre_archivo', 'tipo_mime', 'peso_bytes', 'fecha_subida')
    search_fields = ('nombre_archivo',)
