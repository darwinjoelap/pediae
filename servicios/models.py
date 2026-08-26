from django.db import models
from tenant.models import Tenant


class TasaCambio(models.Model):
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE,
        related_name='tasa_cambio', verbose_name='Consultorio'
    )
    tasa = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Tasa Bs/USD',
        help_text='Ej: 46.50 — bolívares por dólar'
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tasa de cambio'
        verbose_name_plural = 'Tasas de cambio'

    def __str__(self):
        return f'Bs {self.tasa} / USD — {self.tenant.nombre}'


class Servicio(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE,
        related_name='servicios', verbose_name='Consultorio'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre del servicio')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    precio_usd = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='Precio (USD)'
    )
    costo_adquisicion_usd = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True, default=None,
        verbose_name='Costo de adquisición (USD)',
        help_text='Ej: vacunas. Opcional. Se usa para calcular el ingreso real.'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']
        unique_together = [['tenant', 'nombre']]

    def __str__(self):
        return f'{self.nombre} — ${self.precio_usd}'

    def precio_bs(self, tasa):
        if not tasa:
            return None
        return round(float(self.precio_usd) * float(tasa), 2)