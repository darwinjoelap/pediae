from django.db import models
from django.utils import timezone
from django.conf import settings


class Plan(models.Model):
    MENSUAL = 'mensual'
    ANUAL = 'anual'
    TIPO_CHOICES = [
        (MENSUAL, 'Mensual'),
        (ANUAL, 'Anual'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=MENSUAL)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    max_pacientes = models.IntegerField(default=500)
    max_usuarios = models.IntegerField(default=3)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'


class Tenant(models.Model):
    # Identificación
    nombre = models.CharField(max_length=200, verbose_name='Nombre del consultorio')
    slug = models.SlugField(unique=True, verbose_name='Identificador único',
        help_text='Se usará en la URL: /t/slug/')

    # Contacto
    email = models.EmailField(verbose_name='Email de contacto')
    telefono = models.CharField(max_length=30, blank=True)

    # Control
    activo = models.BooleanField(default=False, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def app_url(self):
        base = getattr(settings, 'APP_BASE_URL',
            'https://ginea-saas-production.up.railway.app')
        return f'{base}/t/{self.slug}/'

    @property
    def suscripcion_activa(self):
        return self.suscripciones.filter(
            estado='activa',
            fecha_fin__gte=timezone.now().date()
        ).first()


class Suscripcion(models.Model):
    ACTIVA = 'activa'
    VENCIDA = 'vencida'
    SUSPENDIDA = 'suspendida'
    TRIAL = 'trial'
    ESTADO_CHOICES = [
        (ACTIVA, 'Activa'),
        (VENCIDA, 'Vencida'),
        (SUSPENDIDA, 'Suspendida'),
        (TRIAL, 'Trial'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,
        related_name='suscripciones')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default=TRIAL)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    renovacion_automatica = models.BooleanField(default=False)
    notas = models.TextField(blank=True, verbose_name='Notas internas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-fecha_fin']

    def __str__(self):
        return f'{self.tenant} — {self.plan} ({self.get_estado_display()})'

    @property
    def dias_restantes(self):
        delta = self.fecha_fin - timezone.now().date()
        return delta.days

    @property
    def esta_vigente(self):
        return self.estado == self.ACTIVA and self.fecha_fin >= timezone.now().date()