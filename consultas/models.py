from django.db import models
from pacientes.models import Paciente
from agenda.models import Cita


class Consulta(models.Model):
    TIPO_CONSULTA_CHOICES = [
        ('control_sano', 'Control sano'),
        ('enfermedad', 'Consulta por enfermedad'),
        ('seguimiento', 'Seguimiento'),
    ]
    CLASIFICACION_NUTRICIONAL_CHOICES = [
        ('desnutricion_severa', 'Desnutrición severa (<p3)'),
        ('desnutricion', 'Desnutrición (p3-p10)'),
        ('riesgo_desnutricion', 'Riesgo de desnutrición (p10-p15)'),
        ('eutrofico', 'Eutrófico (p15-p85)'),
        ('sobrepeso', 'Sobrepeso (p85-p97)'),
        ('obesidad', 'Obesidad (>p97)'),
    ]

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
    tipo_consulta = models.CharField(
        max_length=20,
        choices=TIPO_CONSULTA_CHOICES,
        default='control_sano',
        verbose_name='Tipo de consulta',
    )

    # S — Subjetivo
    motivo_consulta = models.TextField(blank=True, verbose_name='Motivo de consulta')
    sintomas_actuales = models.TextField(blank=True, verbose_name='Enfermedad actual / síntomas')

    # O — Objetivo: Signos vitales
    peso = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True, verbose_name='Peso (kg)'
    )
    talla = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True, verbose_name='Talla / Longitud (cm)'
    )
    perimetro_cefalico = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True, verbose_name='Perímetro cefálico (cm)'
    )
    frecuencia_cardiaca = models.IntegerField(
        null=True, blank=True, verbose_name='Frecuencia cardíaca (lpm)'
    )
    frecuencia_respiratoria = models.IntegerField(
        null=True, blank=True, verbose_name='Frecuencia respiratoria (rpm)'
    )
    temperatura = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True, verbose_name='Temperatura (°C)'
    )
    saturacion_oxigeno = models.IntegerField(
        null=True, blank=True, verbose_name='Saturación O₂ (%)'
    )
    tension_arterial = models.CharField(
        max_length=20, blank=True, verbose_name='Tensión arterial'
    )

    # Percentiles OMS (calculados al guardar)
    percentil_peso = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True, verbose_name='Percentil peso/edad (OMS)'
    )
    percentil_talla = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True, verbose_name='Percentil talla/edad (OMS)'
    )
    percentil_pc = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True, verbose_name='Percentil PC/edad (OMS)'
    )
    clasificacion_nutricional = models.CharField(
        max_length=30,
        choices=CLASIFICACION_NUTRICIONAL_CHOICES,
        blank=True,
        verbose_name='Clasificación nutricional',
    )

    # O — Objetivo: Examen físico
    examen_fisico = models.TextField(
        blank=True, verbose_name='Examen físico'
    )
    desarrollo_psicomotor = models.TextField(
        blank=True, verbose_name='Desarrollo psicomotor'
    )

    # A — Análisis
    diagnostico = models.TextField(verbose_name='Diagnóstico / Impresión diagnóstica')

    # P — Plan
    tratamiento = models.TextField(blank=True, verbose_name='Tratamiento / Plan')
    indicaciones = models.TextField(
        blank=True, verbose_name='Indicaciones',
        help_text='Instrucciones específicas para el paciente o representante',
    )
    laboratorio = models.TextField(blank=True, verbose_name='Exámenes paraclínicos solicitados')
    proxima_cita = models.DateField(null=True, blank=True, verbose_name='Próxima cita')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    # ── Hábitos (alimentación, sueño, eliminación) ──────────────────────────
    ALIMENTACION_CHOICES = [
        ('lme', 'Lactancia materna exclusiva'),
        ('mixta', 'Lactancia mixta'),
        ('formula', 'Fórmula exclusiva'),
        ('complementaria', 'Alimentación complementaria + lactancia'),
        ('familiar', 'Dieta familiar'),
    ]
    APETITO_CHOICES = [
        ('bueno', 'Bueno'),
        ('regular', 'Regular'),
        ('malo', 'Malo / hiporexia'),
    ]
    DEPOSICIONES_CHOICES = [
        ('varias_dia', 'Varias veces al día'),
        ('una_dia', 'Una vez al día'),
        ('cada_2_3', 'Cada 2-3 días'),
        ('estreñimiento', 'Estreñimiento (>3 días)'),
    ]
    CONSISTENCIA_CHOICES = [
        ('normal', 'Normal / pastosa'),
        ('blanda', 'Blanda / semilíquida'),
        ('liquida', 'Líquida / diarrea'),
        ('dura', 'Dura / caprinas'),
    ]

    tipo_alimentacion = models.CharField(
        max_length=20, choices=ALIMENTACION_CHOICES,
        blank=True, verbose_name='Tipo de alimentación',
    )
    apetito = models.CharField(
        max_length=10, choices=APETITO_CHOICES,
        blank=True, verbose_name='Apetito',
    )
    num_comidas = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Número de comidas al día',
    )
    notas_alimentacion = models.TextField(
        blank=True, verbose_name='Notas de alimentación',
        help_text='Alimentos rechazados, alergias alimentarias, hábitos especiales',
    )

    horas_sueno_nocturno = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Horas de sueño nocturno',
    )
    num_siestas = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Número de siestas al día',
    )
    duracion_siesta = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Duración de siesta (min)',
    )
    notas_sueno = models.TextField(
        blank=True, verbose_name='Notas de sueño',
        help_text='Ronquidos, despertares frecuentes, pesadillas, comparte cama',
    )

    frecuencia_deposiciones = models.CharField(
        max_length=15, choices=DEPOSICIONES_CHOICES,
        blank=True, verbose_name='Frecuencia de deposiciones',
    )
    consistencia_deposiciones = models.CharField(
        max_length=10, choices=CONSISTENCIA_CHOICES,
        blank=True, verbose_name='Consistencia de deposiciones',
    )
    control_esfinteres = models.BooleanField(
        null=True, blank=True,
        verbose_name='Control de esfínteres logrado',
    )
    notas_eliminacion = models.TextField(
        blank=True, verbose_name='Notas de eliminación',
        help_text='Hematuria, disuria, enuresis, encopresis',
    )

    # Pago
    pagado = models.BooleanField(default=False, verbose_name='Pagado')
    notas_pago = models.CharField(max_length=200, blank=True, verbose_name='Notas de pago')

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f'{self.get_tipo_consulta_display()} — {self.paciente.nombre_completo} ({self.fecha})'

    def calcular_edad_en_meses(self):
        """Retorna la edad del paciente en meses a la fecha de la consulta."""
        if not self.paciente.fecha_nacimiento or not self.fecha:
            return None
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(self.fecha, self.paciente.fecha_nacimiento)
        return delta.years * 12 + delta.months

    def calcular_percentiles(self):
        """Calcula percentiles OMS para peso, talla y PC según edad y sexo."""
        from .oms import calcular_percentil_oms
        edad_meses = self.calcular_edad_en_meses()
        if edad_meses is None:
            return
        sexo = getattr(self.paciente, 'sexo', None)
        if self.peso:
            self.percentil_peso = calcular_percentil_oms('peso', edad_meses, float(self.peso), sexo)
        if self.talla:
            self.percentil_talla = calcular_percentil_oms('talla', edad_meses, float(self.talla), sexo)
        if self.perimetro_cefalico and edad_meses <= 36:
            self.percentil_pc = calcular_percentil_oms('pc', edad_meses, float(self.perimetro_cefalico), sexo)
        self._set_clasificacion_nutricional()

    def _set_clasificacion_nutricional(self):
        p = self.percentil_peso
        if p is None:
            return
        if p < 3:
            self.clasificacion_nutricional = 'desnutricion_severa'
        elif p < 10:
            self.clasificacion_nutricional = 'desnutricion'
        elif p < 15:
            self.clasificacion_nutricional = 'riesgo_desnutricion'
        elif p <= 85:
            self.clasificacion_nutricional = 'eutrofico'
        elif p <= 97:
            self.clasificacion_nutricional = 'sobrepeso'
        else:
            self.clasificacion_nutricional = 'obesidad'

    def save(self, *args, **kwargs):
        self.calcular_percentiles()
        super().save(*args, **kwargs)

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
    costo_adquisicion_usd = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True, default=None,
        verbose_name='Costo adquisición USD al momento',
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

    @property
    def puede_eliminar(self):
        from datetime import date, timedelta
        return self.creado_en.date() >= date.today() - timedelta(days=7)

    def __str__(self):
        return f'{self.servicio.nombre} — {self.paciente.nombre_completo} ({self.fecha})'
