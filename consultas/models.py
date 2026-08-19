from django.db import models
from pacientes.models import Paciente
from agenda.models import Cita


class Consulta(models.Model):
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='consultas',
        verbose_name='Consultorio',
    )
    medico = models.ForeignKey(
        'accounts.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='consultas_atendidas',
        verbose_name='Médico',
        limit_choices_to={'rol': 'medico'},
    )
    lugar = models.ForeignKey(
        'agenda.LugarConsulta', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='consultas', verbose_name='Lugar de consulta'
    )
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE,
        related_name='consultas', verbose_name='Paciente'
    )
    cita = models.OneToOneField(
        Cita, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='consulta', verbose_name='Cita asociada'
    )
    fecha = models.DateField(verbose_name='Fecha de consulta')
    motivo_consulta = models.TextField(blank=True, verbose_name='Motivo / notas adicionales')
    sintomas_actuales = models.TextField(verbose_name='Síntomas actuales', blank=True)
    examen_fisico = models.TextField(verbose_name='Examen físico', blank=True)
    ecografia = models.TextField(blank=True, verbose_name='Ecografía')
    colposcopia = models.TextField(blank=True, verbose_name='Colposcopia')
    imagenes = models.TextField(
        blank=True,
        verbose_name='Imágenes',
        help_text='Mamografía, ecografía, densitometría ósea, etc.',
    )
    diagnostico = models.TextField(verbose_name='Diagnóstico')
    tratamiento = models.TextField(verbose_name='Tratamiento')
    proxima_cita = models.DateField(null=True, blank=True, verbose_name='Próxima cita')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Peso (kg)')
    tension_arterial = models.CharField(max_length=20, blank=True, verbose_name='Tensión arterial')
    es_prenatal = models.BooleanField(default=False, verbose_name='Es control prenatal')
    fpp = models.DateField(null=True, blank=True, verbose_name='FPP (Fecha probable de parto)')
    semanas_gestacion = models.IntegerField(null=True, blank=True, verbose_name='Semanas de gestación')
    altura_uterina = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Altura uterina (cm)')
    fcf = models.IntegerField(null=True, blank=True, verbose_name='FCF (Frecuencia cardíaca fetal, lpm)')
    presentacion_fetal = models.CharField(max_length=50, blank=True, verbose_name='Presentación fetal')
    edemas = models.BooleanField(null=True, blank=True, verbose_name='Edemas')
    laboratorio = models.TextField(blank=True, verbose_name='Laboratorio')

    # Pago
    pagado = models.BooleanField(default=False, verbose_name='Pagado')
    notas_pago = models.CharField(max_length=200, blank=True, verbose_name='Notas de pago')

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        tipo = 'Prenatal' if self.es_prenatal else 'Consulta'
        return f'{tipo} — {self.paciente.nombre_completo} ({self.fecha})'

    @property
    def total_usd(self):
        return sum(s.precio_usd for s in self.servicios_usados.all())

    @property
    def total_bs(self):
        servicios = self.servicios_usados.all()
        if not servicios:
            return None
        total = sum(
            float(s.precio_usd) * float(s.tasa_cambio)
            for s in servicios if s.tasa_cambio
        )
        return round(total, 2) if total else None


class AdjuntoConsulta(models.Model):
    TIPO_CHOICES = [
        ('imagen', 'Imagen'),
        ('pdf', 'PDF'),
    ]
    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE,
        related_name='adjuntos', verbose_name='Consulta'
    )
    drive_file_id = models.CharField(max_length=500, verbose_name='ID de archivo en Drive')
    nombre_original = models.CharField(max_length=255, verbose_name='Nombre del archivo')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    drive_folder_id = models.CharField(max_length=100, blank=True, verbose_name='ID de carpeta en Drive')
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Adjunto'
        verbose_name_plural = 'Adjuntos'
        ordering = ['subido_en']

    def __str__(self):
        return f'{self.nombre_original} ({self.consulta})'

    def get_url(self):
        from consultas.drive import configurar_cloudinary
        import cloudinary
        configurar_cloudinary()
        cloud = cloudinary.config().cloud_name
        if self.tipo == 'pdf':
            return f"https://res.cloudinary.com/{cloud}/raw/upload/{self.drive_file_id}"
        return cloudinary.CloudinaryResource(self.drive_file_id).build_url()

    def get_thumbnail_url(self):
        from consultas.drive import configurar_cloudinary
        import cloudinary
        configurar_cloudinary()
        if self.tipo == 'imagen':
            return cloudinary.CloudinaryResource(self.drive_file_id).build_url(
                width=300, height=300, crop='fill'
            )
        return None


class ConsultaServicio(models.Model):
    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE,
        related_name='servicios_usados'
    )
    servicio = models.ForeignKey(
        'servicios.Servicio', on_delete=models.PROTECT,
        related_name='consultas'
    )
    precio_usd = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='Precio USD al momento'
    )
    tasa_cambio = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name='Tasa al momento'
    )

    class Meta:
        verbose_name = 'Servicio de consulta'
        verbose_name_plural = 'Servicios de consulta'

    def __str__(self):
        return f'{self.servicio.nombre} — ${self.precio_usd}'

    @property
    def precio_bs(self):
        if self.tasa_cambio:
            return round(float(self.precio_usd) * float(self.tasa_cambio), 2)
        return None

class Procedimiento(models.Model):
    tenant = models.ForeignKey(
        'tenant.Tenant', on_delete=models.CASCADE,
        related_name='procedimientos'
    )
    paciente = models.ForeignKey(
        'pacientes.Paciente', on_delete=models.CASCADE,
        related_name='procedimientos'
    )
    cita = models.OneToOneField(
        'agenda.Cita', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='procedimiento'
    )
    medico = models.ForeignKey(
        'accounts.Usuario', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='procedimientos'
    )
    fecha = models.DateField()
    servicio = models.ForeignKey(
        'servicios.Servicio', on_delete=models.PROTECT,
        related_name='procedimientos'
    )
    precio_usd = models.DecimalField(max_digits=8, decimal_places=2)
    tasa_cambio = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    notas = models.TextField(blank=True, verbose_name='Notas')
    pagado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Procedimiento'
        verbose_name_plural = 'Procedimientos'
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f'{self.servicio.nombre} — {self.paciente.nombre_completo} ({self.fecha})'