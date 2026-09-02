from django.db import models
from django.conf import settings
from pacientes.models import Paciente


class LugarConsulta(models.Model):
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='lugares',
        verbose_name='Consultorio',
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre del lugar')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    direccion = models.CharField(max_length=200, blank=True, verbose_name='Dirección')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono del lugar')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    orden = models.PositiveSmallIntegerField(default=0, verbose_name='Orden en listas')

    class Meta:
        verbose_name = 'Lugar de consulta'
        verbose_name_plural = 'Lugares de consulta'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('confirmada', 'Confirmada'),
        ('atendida', 'Atendida'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No asistió'),
    ]
    ESTADO_COLORES = {
        'programada': 'primary',
        'confirmada': 'success',
        'atendida': 'secondary',
        'cancelada': 'danger',
        'no_asistio': 'warning',
    }
    CANAL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('ambos', 'WhatsApp y Email'),
    ]

    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='citas',
        verbose_name='Consultorio',
    )
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE,
        related_name='citas', verbose_name='Paciente'
    )
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora de inicio')
    hora_fin = models.TimeField(null=True, blank=True, verbose_name='Hora de fin')
    motivo = models.CharField(max_length=200, blank=True, verbose_name='Motivo de la cita')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES,
        default='programada', verbose_name='Estado'
    )
    lugar = models.ForeignKey(
        LugarConsulta, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='citas', verbose_name='Lugar de consulta'
    )
    servicios = models.ManyToManyField(
    'servicios.Servicio',
    blank=True,
    related_name='citas',
    verbose_name='Servicios esperados',
)
    notas = models.TextField(blank=True, verbose_name='Notas')
    recordatorio_enviado = models.BooleanField(default=False, verbose_name='Recordatorio enviado')
    recordatorio_fecha = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de envío')
    recordatorio_canal = models.CharField(
        max_length=10, choices=CANAL_CHOICES,
        blank=True, verbose_name='Canal usado'
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='citas_creadas', verbose_name='Creado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f'{self.paciente.nombre_completo} — {self.fecha} {self.hora_inicio}'

    def get_color(self):
        return self.ESTADO_COLORES.get(self.estado, 'secondary')

    def _get_consultorio_info(self):
        try:
            tenant = self.tenant or (self.creado_por.tenant if self.creado_por else None)
            if tenant:
                config = tenant.config
                nombre = getattr(config, 'nombre_consultorio', '') or tenant.nombre
                return nombre, config.telefono or tenant.telefono
            return 'nuestro consultorio', ''
        except Exception:
            return 'nuestro consultorio', ''

    def _destinatario_whatsapp(self):
        """
        Determina a quién va dirigido el recordatorio: si el paciente tiene
        representante registrado (caso pediátrico), el mensaje se dirige a
        él/ella y se envía a su teléfono; si no, se dirige al propio paciente.
        Devuelve (nombre_saludo, telefono_destino, representante_o_None).
        """
        paciente = self.paciente
        representante = (getattr(paciente, 'nombre_representante', '') or '').strip()
        if representante:
            telefono = (getattr(paciente, 'telefono_representante', '') or '').strip() or paciente.telefono
            return representante.split()[0], telefono, representante
        return paciente.nombre_completo.split()[0], paciente.telefono, None

    def get_whatsapp_url(self, tenant=None):
        import urllib.parse
        import re

        def _fmt_hora(t):
            """Hora en formato 12 h sin cero inicial: '2:30 pm'."""
            return t.strftime('%I:%M %p').lstrip('0').lower()

        tenant = tenant or self.tenant
        nombre_saludo, telefono, representante = self._destinatario_whatsapp()
        # Eliminar todo lo que no sea dígito o '+' (incluye caracteres Unicode invisibles)
        telefono_limpio = re.sub(r'[^\d+]', '', telefono)
        if telefono_limpio.startswith('0'):
            telefono_limpio = '+58' + telefono_limpio[1:]
        elif not telefono_limpio.startswith('+'):
            telefono_limpio = '+58' + telefono_limpio

        if self.lugar:
            lugar_str = f' en {self.lugar.nombre}'
            if self.lugar.direccion:
                lugar_str += f' ({self.lugar.direccion})'
        else:
            lugar_str = ''

        try:
            config = tenant.config if tenant else None
        except Exception:
            config = None
        nombre_consultorio = (
            (getattr(config, 'nombre_consultorio', '') if config else '')
            or (tenant.nombre if tenant else '')
            or 'nuestro consultorio'
        )

        if representante:
            cuerpo = (
                f'le recordamos la cita de {self.paciente.nombre_completo} con {nombre_consultorio} '
                f'el {self.fecha.strftime("%d/%m/%Y")} a las {_fmt_hora(self.hora_inicio)}{lugar_str}.'
            )
        else:
            cuerpo = (
                f'le recordamos su cita con {nombre_consultorio} '
                f'el {self.fecha.strftime("%d/%m/%Y")} a las {_fmt_hora(self.hora_inicio)}{lugar_str}.'
            )

        if config and config.whatsapp_mensaje:
            mensaje = f'Hola {nombre_saludo}, {cuerpo}\n\n{config.whatsapp_mensaje}'
        else:
            mensaje = f'Hola {nombre_saludo}, {cuerpo} Por favor confirme su asistencia. Gracias.'

        return f'https://wa.me/{telefono_limpio}?text={urllib.parse.quote(mensaje)}'

    def get_email_asunto(self):
        return f'Recordatorio de cita — {self.fecha.strftime("%d/%m/%Y")}'

    def get_email_cuerpo(self):
        nombre_consultorio, telefono_consultorio = self._get_consultorio_info()
        lugar_str = f'\nLugar: {self.lugar.nombre}' if self.lugar else ''
        nombre = self.paciente.nombre_completo.split()[0]
        return (
            f'Estimada {nombre},\n\n'
            f'Le recordamos su cita médica con {nombre_consultorio}:\n\n'
            f'Fecha: {self.fecha.strftime("%d/%m/%Y")}\n'
            f'Hora: {self.hora_inicio.strftime("%H:%M")}{lugar_str}\n\n'
            f'Por favor confirme su asistencia respondiendo este mensaje.\n\n'
            f'Atentamente,\n{nombre_consultorio}\n{telefono_consultorio}'
        )
