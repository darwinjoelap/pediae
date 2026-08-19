"""
Integración con Cloudinary para almacenamiento de archivos adjuntos.
Organiza los archivos por paciente y consulta usando carpetas (public_id).
"""
import cloudinary
import cloudinary.uploader
from decouple import config


def configurar_cloudinary():
    cloudinary.config(
        cloud_name=config('CLOUDINARY_CLOUD_NAME'),
        api_key=config('CLOUDINARY_API_KEY'),
        api_secret=config('CLOUDINARY_API_SECRET'),
        secure=True,
    )


def subir_archivo_drive(archivo, consulta):
    """
    Sube un archivo a Cloudinary organizado por paciente y consulta.
    Mantiene la misma interfaz que la versión de Google Drive.
    """
    configurar_cloudinary()

    paciente = consulta.paciente
    fecha_str = consulta.fecha.strftime('%Y-%m-%d')

    # Organizar en carpetas: ginea/cedula-nombre/fecha-consulta/
    cedula_limpia = paciente.cedula.replace('-', '').replace('/', '')
    nombre_limpio = paciente.nombre_completo.replace(' ', '_').replace('/', '')[:30]
    carpeta = f"ginea/{cedula_limpia}_{nombre_limpio}/{fecha_str}_consulta"

    # Determinar tipo de recurso
    es_imagen = archivo.content_type.startswith('image/')
    resource_type = 'image' if es_imagen else 'raw'

    resultado = cloudinary.uploader.upload(
        archivo,
        folder=carpeta,
        resource_type=resource_type,
        use_filename=True,
        unique_filename=True,
        type='upload',
        access_mode='public',
        upload_preset='ginea_public',
    )

    return {
        'file_id': resultado['public_id'],
        'folder_id': carpeta,
        'url': resultado['secure_url'],
        'resource_type': resource_type,
    }


def get_url(public_id, resource_type='image'):
    """Genera URL de acceso al archivo."""
    configurar_cloudinary()
    if resource_type == 'raw':
        return cloudinary.CloudinaryResource(public_id, resource_type='raw').build_url()
    return cloudinary.CloudinaryResource(public_id).build_url()