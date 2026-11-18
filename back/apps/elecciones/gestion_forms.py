"""Formularios de gestión MVT de Elecciones (ED2, CA2, VO2-VO3, OP2).

El estado nunca se edita en un formulario: cambia solo por las
transiciones de ``elecciones.ciclo``. Lo que se puede editar depende del
estado de la edición:

- BORRADOR: todo (estructura, fechas y textos).
- PROGRAMADA y siguientes: solo cambios menores (textos); la estructura
  y las fechas quedan fijas.
- FINALIZADA: nada.
"""

from django import forms

from .ciclo import errores_de_fechas_votacion
from .models import Categoria, Edicion, Opcion, Votacion

FORMATO_FECHA = '%Y-%m-%dT%H:%M'


def _widget_fecha():
    return forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=FORMATO_FECHA)


def _bloquear(form, campos, motivo):
    """Deshabilita campos: Django ignora lo que llegue por POST para ellos."""
    for nombre in campos:
        if nombre in form.fields:
            form.fields[nombre].disabled = True
            form.fields[nombre].help_text = motivo


class EdicionForm(forms.ModelForm):
    """Alta/edición de una edición: nombre, año y periodo.

    El periodo es obligatorio: es lo que abre y cierra la edición sola.
    """

    nombre = forms.CharField(max_length=150, label='Nombre')
    anio = forms.IntegerField(min_value=2020, max_value=2100, label='Año')
    fecha_inicio = forms.DateTimeField(
        label='Inicio',
        widget=_widget_fecha(),
        help_text='Al llegar esta fecha, la edición programada se activa sola.',
    )
    fecha_fin = forms.DateTimeField(
        label='Fin',
        widget=_widget_fecha(),
        help_text='Al llegar esta fecha, la edición se cierra sola.',
    )

    class Meta:
        model = Edicion
        fields = ('nombre', 'anio', 'fecha_inicio', 'fecha_fin')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.estado != Edicion.BORRADOR:
            _bloquear(
                self,
                ('anio', 'fecha_inicio', 'fecha_fin'),
                'Fijo desde que la edición se programó.',
            )

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        anio = cleaned.get('anio')
        inicio = cleaned.get('fecha_inicio')
        fin = cleaned.get('fecha_fin')

        # ED2: nombre + año único con error legible, no un 500.
        if nombre and anio is not None:
            existe = (
                Edicion.objects.filter(nombre__iexact=nombre, anio=anio)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if existe:
                self.add_error('nombre', f'Ya existe una edición «{nombre} {anio}».')

        if inicio and fin and inicio >= fin:
            self.add_error('fecha_fin', 'El fin debe ser posterior al inicio.')
        elif inicio and fin and self.instance.pk:
            # R2: el periodo nuevo debe seguir conteniendo a sus votaciones.
            fuera = [
                v.nombre
                for v in self.instance.votaciones.all()
                if v.fecha_apertura < inicio or v.fecha_cierre > fin
            ]
            if fuera:
                self.add_error(
                    'fecha_fin',
                    'Estas votaciones quedarían por fuera del periodo: '
                    + ', '.join(fuera) + '. Ajusta primero sus fechas.',
                )
        return cleaned


class CierreAnticipadoForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo del cierre',
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Obligatorio. Queda registrado en la edición y en la auditoría.',
    )

    def clean_motivo(self):
        motivo = self.cleaned_data['motivo'].strip()
        if len(motivo) < 10:
            raise forms.ValidationError('Describe el motivo con al menos 10 caracteres.')
        return motivo


class CategoriaForm(forms.ModelForm):
    """Alta/edición de categoría con nombre único (CA2).

    Si ya se usó en una edición finalizada, el nombre queda fijo para no
    reescribir el historial: solo se edita la descripción.
    """

    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.usada_en_edicion_finalizada:
            _bloquear(
                self,
                ('nombre',),
                'Se usó en una edición finalizada: el nombre no cambia para conservar el historial.',
            )

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
    """Alta/edición de votación (VO2).

    Solo se crean votaciones en ediciones en BORRADOR. Una vez programada la
    edición, la votación conserva su categoría y fechas: se editan textos.
    """

    class Meta:
        model = Votacion
        fields = (
            'edicion',
            'categoria',
            'nombre',
            'descripcion',
            'fecha_apertura',
            'fecha_cierre',
            'mostrar_resultados_en_vivo',
        )
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
            'fecha_apertura': _widget_fecha(),
            'fecha_cierre': _widget_fecha(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instancia = self.instance

        categorias = Categoria.objects.filter(archivada=False)
        if instancia.pk:
            # Se conserva la actual aunque luego se haya archivado.
            categorias = categorias | Categoria.objects.filter(pk=instancia.categoria_id)
        self.fields['categoria'].queryset = categorias.order_by('nombre')

        if instancia.pk:
            # Una votación no se muda de edición.
            _bloquear(self, ('edicion',), 'La edición de una votación no cambia.')
            if not instancia.edicion.admite_cambios_de_estructura:
                _bloquear(
                    self,
                    ('categoria', 'fecha_apertura', 'fecha_cierre'),
                    'Fijo desde que la edición se programó.',
                )
        else:
            self.fields['edicion'].queryset = Edicion.objects.filter(
                estado=Edicion.BORRADOR
            ).order_by('-anio', 'nombre')
            self.fields['edicion'].help_text = (
                'Solo ediciones en borrador: después de programar, la estructura queda fija.'
            )

    def clean(self):
        cleaned = super().clean()
        edicion = cleaned.get('edicion') or (self.instance.edicion if self.instance.pk else None)
        categoria = cleaned.get('categoria')
        nombre = (cleaned.get('nombre') or '').strip()

        # VO3 + R2: apertura < cierre y dentro del periodo de la edición.
        for error in errores_de_fechas_votacion(
            edicion, cleaned.get('fecha_apertura'), cleaned.get('fecha_cierre')
        ):
            self.add_error('fecha_cierre', error)

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


class EdicionCategoriaForm(forms.Form):
    """Agrega una categoría a una edición creando su primera votación.

    En el modelo una categoría pertenece a la edición a través de sus
    votaciones, así que agregarla es crear una votación en ella. Se puede
    elegir una categoría existente (no archivada) o escribir una nueva.
    """

    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.none(),
        required=False,
        label='Categoría existente',
        empty_label='— Crear una categoría nueva —',
    )
    nueva_categoria = forms.CharField(
        max_length=150,
        required=False,
        label='Nombre de la categoría nueva',
        help_text='Solo si no eliges una existente. Ej.: Piqueria, Rey Infantil.',
    )
    nombre_votacion = forms.CharField(
        max_length=150,
        label='Nombre de la votación',
        help_text='Ej.: Rey de la Piqueria 2026.',
    )
    fecha_apertura = forms.DateTimeField(label='Apertura', widget=_widget_fecha())
    fecha_cierre = forms.DateTimeField(label='Cierre', widget=_widget_fecha())

    def __init__(self, *args, edicion=None, puede_crear_categoria=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.edicion = edicion
        self.puede_crear_categoria = puede_crear_categoria
        # Solo se ofrecen las categorías activas que la edición todavía no usa.
        usadas = edicion.votaciones.values_list('categoria_id', flat=True) if edicion else []
        self.fields['categoria'].queryset = (
            Categoria.objects.filter(archivada=False).exclude(pk__in=usadas).order_by('nombre')
        )

    def clean(self):
        cleaned = super().clean()
        categoria = cleaned.get('categoria')
        nueva = (cleaned.get('nueva_categoria') or '').strip()

        if categoria and nueva:
            self.add_error(
                'nueva_categoria',
                'Elige una categoría existente o escribe una nueva, no las dos.',
            )
        elif not categoria and not nueva:
            self.add_error('categoria', 'Elige una categoría o escribe el nombre de una nueva.')
        elif nueva:
            if not self.puede_crear_categoria:
                self.add_error('nueva_categoria', 'No tienes permiso para crear categorías.')
            else:
                existente = Categoria.objects.filter(nombre__iexact=nueva).first()
                if existente:
                    detalle = ' (está archivada)' if existente.archivada else ': elígela en la lista'
                    self.add_error(
                        'nueva_categoria',
                        f'La categoría «{existente.nombre}» ya existe{detalle}.',
                    )
        cleaned['nueva_categoria'] = nueva

        for error in errores_de_fechas_votacion(
            self.edicion, cleaned.get('fecha_apertura'), cleaned.get('fecha_cierre')
        ):
            self.add_error('fecha_cierre', error)
        return cleaned


class OpcionForm(forms.ModelForm):
    """Creación/edición de una opción dentro de una votación (OP2).

    Con la votación LISTA (edición ya programada) solo se corrigen textos:
    la casilla y el voto en blanco quedan fijos.
    """

    class Meta:
        model = Opcion
        fields = ('nombre', 'subtitulo', 'descripcion', 'orden', 'es_voto_blanco')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, votacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.votacion = votacion
        if votacion is not None and votacion.estado != Votacion.BORRADOR:
            _bloquear(
                self,
                ('orden', 'es_voto_blanco'),
                'Fijo desde que la edición se programó.',
            )

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
