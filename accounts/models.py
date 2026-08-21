from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_MEDICO = 'medico'
    ROL_ASISTENTE = 'asistente'
    ROL_CHOICES = [
        (ROL_MEDICO, 'Médico'),
        (ROL_ASISTENTE, 'Asistente'),
    ]

    SEXO_MASCULINO = 'M'
    SEXO_FEMENINO = 'F'
    SEXO_CHOICES = [
        (SEXO_MASCULINO, 'Masculino'),
        (SEXO_FEMENINO, 'Femenino'),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default=ROL_ASISTENTE,
        verbose_name='Rol',
    )
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        default=SEXO_FEMENINO,
        verbose_name='Sexo',
    )
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usuarios',
        verbose_name='Consultorio',
    )

    # Credenciales profesionales (solo médicos)
    especialidad = models.CharField(
        max_length=200, blank=True,
        verbose_name='Especialidad',
        help_text='Ej: Pediatría y Puericultura',
    )
    credenciales = models.CharField(
        max_length=300, blank=True,
        verbose_name='Credenciales / Posgrado',
        help_text='Ej: Especialista en Pediatría. Universidad Central de Venezuela',
    )
    numero_mpps = models.CharField(
        max_length=50, blank=True,
        verbose_name='Número MPPS / CMP',
        help_text='Número de registro médico profesional',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.titulo})'

    @property
    def titulo(self):
        if self.rol == self.ROL_MEDICO:
            return 'Dr.' if self.sexo == self.SEXO_MASCULINO else 'Dra.'
        return 'Asistente'

    @property
    def nombre_completo_con_titulo(self):
        nombre = self.get_full_name() or self.username
        return f'{self.titulo} {nombre}'

    @property
    def es_medico(self):
        return self.rol == self.ROL_MEDICO

    @property
    def es_doctora(self):
        """Compatibilidad con código existente."""
        return self.rol == self.ROL_MEDICO

    @property
    def es_asistente(self):
        return self.rol == self.ROL_ASISTENTE
