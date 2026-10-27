"""Formularios de gestión MVT de Elecciones (ED2, CA2, VO2-VO3, OP2)."""

from django import forms

from .models import Categoria, Edicion, Opcion, Votacion


class EdicionForm(forms.ModelForm):
    """Alta/edición de una edición con el año obligatorio y estado en arco."""

    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PROGRAMADA', 'Programada'),
        ('ACTIVA', 'Activa'),
        ('CERRANDO', 'Cerrando'),
        ('FINALIZADA', 'Finalizada'),
    ]

    nombre = forms.CharField(max_length=150, label='Nombre')
    anio = forms.IntegerField(min_value=2020, max_value=2100, label='Año')
    estado = forms.ChoiceField(choices=Edicion.ESTADOS, label='Estado')

    class Meta:
        model = Edicion
        fields = ('nombre', 'anio', 'estado')

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        anio = cleaned.get('anio')

        # ED2: nombre + año único con error legible, no un 500.
        if nombre and anio is not None:
            existe = (
                Edicion.objects.filter(nombre__iexact=nombre, anio=anio)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if existe:
                self.add_error('nombre', f'Ya existe una edición «{nombre} {anio}».')
        return cleaned


class CategoriaForm(forms.ModelForm):
    """Alta/edición de categoría con nombre único (CA2)."""

    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()

        if nombre:
            existe = (
                Categoria.objects.filter(nombre__iexact=nombre)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if existe:
                self.add_error('nombre', f'La categoría «{nombre}» ya existe.')
        return cleaned


class VotacionForm(forms.ModelForm):
    """Alta/edición de votación con selects de edición y categoría (VO2)."""

    class Meta:
        model = Votacion
        fields = (
            'edicion',
            'categoria',
            'nombre',
            'descripcion',
            'fecha_apertura',
            'fecha_cierre',
            'estado',
            'mostrar_resultados_en_vivo',
        )
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
            'fecha_apertura': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'fecha_cierre': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
        }

    def clean(self):
        cleaned = super().clean()
        edicion = cleaned.get('edicion')
        categoria = cleaned.get('categoria')
        nombre = (cleaned.get('nombre') or '').strip()

        # VO3: la apertura debe ser anterior al cierre.
        apertura = cleaned.get('fecha_apertura')
        cierre = cleaned.get('fecha_cierre')
        if apertura and cierre and apertura >= cierre:
            self.add_error(
                'fecha_cierre',
                'La fecha de cierre debe ser posterior a la de apertura.',
            )

        # VO2: nombre obligatorio y único por edición+categoría+nombre.
        if edicion and categoria and nombre:
            existe = (
                Votacion.objects.filter(edicion=edicion, categoria=categoria)
                .filter(nombre__iexact=nombre)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if existe:
                self.add_error(
                    'nombre',
                    f'Ya existe una votación «{nombre}» en {edicion} → {categoria}.',
                )
        return cleaned


class OpcionForm(forms.ModelForm):
    """Creación/edición de una opción dentro de una votación (OP2)."""

    class Meta:
        model = Opcion
        fields = ('nombre', 'subtitulo', 'descripcion', 'orden', 'es_voto_blanco')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, votacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.votacion = votacion

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        if not nombre:
            self.add_error('nombre', 'El nombre es obligatorio.')

        # OP2: la casilla (orden) es única por votación, con error legible.
        orden = cleaned.get('orden')
        if self.votacion and orden is not None:
            existe = (
                Opcion.objects.filter(votacion=self.votacion, orden=orden)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if existe:
                self.add_error(
                    'orden',
                    f'La casilla {orden} ya está ocupada en esta votación.',
                )
        return cleaned
