"""Fotos de los candidatos: validación y normalización.

Se aceptan JPG, PNG o WEBP de hasta ``FOTO_MAX_BYTES``. Se valida por el
contenido (Pillow abre la imagen), no por la extensión. Toda foto se
recorta al centro en cuadrado, se reduce a ``LADO`` px y se guarda en
JPEG: así todas se ven iguales en el tarjetón y pesan poco. Al re-codificar
también se descartan los metadatos (EXIF, ubicación).
"""

from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

FORMATOS = {'JPEG', 'PNG', 'WEBP'}
LADO = 600


def normalizar_foto(archivo):
    """Valida la imagen subida y devuelve un archivo JPEG cuadrado listo para guardar."""
    maximo = getattr(settings, 'FOTO_MAX_BYTES', 2 * 1024 * 1024)
    if archivo.size > maximo:
        raise ValidationError(f'La foto pesa más de {maximo // (1024 * 1024)} MB.')

    try:
        imagen = Image.open(archivo)
        formato = imagen.format
        imagen.load()
    except (UnidentifiedImageError, OSError):
        raise ValidationError('El archivo no es una imagen válida.')
    if formato not in FORMATOS:
        raise ValidationError('Formato no admitido: usa JPG, PNG o WEBP.')

    imagen = ImageOps.exif_transpose(imagen)  # Respeta la orientación del celular.
    if imagen.mode not in ('RGB', 'L'):
        fondo = Image.new('RGB', imagen.size, (255, 255, 255))
        rgba = imagen.convert('RGBA')
        fondo.paste(rgba, mask=rgba.split()[-1])
        imagen = fondo
    imagen = ImageOps.fit(imagen.convert('RGB'), (LADO, LADO), Image.Resampling.LANCZOS)

    salida = BytesIO()
    imagen.save(salida, 'JPEG', quality=85, optimize=True)
    base = (archivo.name or 'foto').rsplit('.', 1)[0][:60] or 'foto'
    return SimpleUploadedFile(f'{base}.jpg', salida.getvalue(), content_type='image/jpeg')
