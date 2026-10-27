"""Formularios de gestión MVT de Elecciones (ED2, CA2)."""

from django import forms

from .models import Categoria, Edicion


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
