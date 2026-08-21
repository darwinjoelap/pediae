import cloudinary
from django.db import models
from tenant.models import Tenant


class ConfigConsultorio(models.Model):
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE,
        related_name='config', verbose_name='Tenant'
    )

    # Identidad
    nombre_consultorio = models.CharField(max_length=200, blank=True,
        verbose_name='Nombre del consultorio',
        help_text='Ej: Consultorio Pediátrico Santa María')
    nombre_medico = models.CharField(max_length=200, blank=True,
        verbose_name='Nombre del médico',
        help_text='Ej: Dr. Carlos Pérez')
    especialidad = models.CharField(max_length=200, blank=True,
        verbose_name='Especialidad')

    # Logo
    logo_public_id = models.CharField(max_length=500, blank=True,
        verbose_name='Logo (Cloudinary public_id)')

    # Contacto
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    telefono = models.CharField(max_length=30, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email visible')

    # WhatsApp
    whatsapp_numero = models.CharField(max_length=20, blank=True,
        verbose_name='Número WhatsApp',
        help_text='Formato internacional sin +: 584121234567')
    whatsapp_mensaje = models.TextField(blank=True,
        verbose_name='Mensaje por defecto WhatsApp',
        help_text='Texto que se pre-carga al abrir WhatsApp desde la app')

    # Membrete para récipe (imagen banner)
    membrete_public_id = models.CharField(
        max_length=500, blank=True,
        verbose_name='Membrete récipe (Cloudinary public_id)',
        help_text='Imagen banner horizontal para el récipe médico. Si se carga, reemplaza el membrete generado automáticamente.',
    )

    # Apariencia
    color_primario = models.CharField(max_length=7, default='#2AACA8',
        verbose_name='Color primario',
        help_text='Color de botones y acentos')
    color_sidebar = models.CharField(max_length=7, default='#1e1b2e',
        verbose_name='Color de la barra lateral',
        help_text='Fondo del menú lateral')

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del consultorio'
        verbose_name_plural = 'Configuraciones de consultorios'

    def __str__(self):
        return f'Config — {self.tenant.nombre}'

    def nombre_display(self):
        """Nombre que se muestra en la app — consultorio si existe, si no el médico."""
        return self.nombre_consultorio or self.nombre_medico or self.tenant.nombre

    def get_logo_url(self):
        if not self.logo_public_id:
            return None
        import cloudinary
        return cloudinary.CloudinaryResource(self.logo_public_id).build_url(
            width=300, height=300, crop='fit', secure=True
        )

    def get_membrete_url(self):
        if not self.membrete_public_id:
            return None
        import cloudinary
        return cloudinary.CloudinaryResource(self.membrete_public_id).build_url(
            secure=True
        )

    def get_whatsapp_url(self, texto_extra=''):
        if not self.whatsapp_numero:
            return '#'
        import urllib.parse
        mensaje = self.whatsapp_mensaje
        if texto_extra:
            mensaje = f'{mensaje}\n{texto_extra}'
        return f'https://wa.me/{self.whatsapp_numero}?text={urllib.parse.quote(mensaje)}'
