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


class Medicamento(models.Model):

    UNIDAD_CHOICES = [
        ('mL',         'mL (jarabe / gotas)'),
        ('tableta',    'Tableta / cápsula'),
        ('mg',         'mg directo'),
        ('UI',         'Unidades internacionales'),
        ('gotas',      'Gotas'),
        ('puff',       'Puff / inhalación'),
        ('aplicacion', 'Aplicación'),
        ('sobre',      'Sobre'),
    ]

    MODO_CALCULO_CHOICES = [
        ('peso', 'Por peso (mg/kg)'),
        ('fija', 'Dosis fija (puffs, inhalaciones…)'),
        ('edad', 'Por rango de edad'),
    ]

    UNIDAD_DOSIS_KG_CHOICES = [
        ('mg',  'mg/kg'),
        ('mcg', 'mcg/kg'),
        ('UI',  'UI/kg'),
        ('g',   'g/kg'),
    ]

    tenant = models.ForeignKey(
        'tenant.Tenant', on_delete=models.CASCADE,
        related_name='medicamentos', verbose_name='Tenant'
    )
    nombre  = models.CharField(max_length=200, verbose_name='Nombre')
    activo  = models.BooleanField(default=True, verbose_name='Activo')
    orden   = models.IntegerField(default=0, verbose_name='Orden')

    # ── Plantilla de indicaciones (soporta tokens {{DOSIS}}, {{FRECUENCIA}}, etc.)
    indicaciones = models.TextField(
        verbose_name='Plantilla de indicaciones',
        blank=True,
        help_text=(
            'Texto libre. Inserta variables automáticas con los botones: '
            '{{DOSIS}}, {{DOSIS_MG}}, {{FRECUENCIA}}, {{DURACION}}, '
            '{{PRESENTACION}}, {{NOMBRE}}, {{PESO}}'
        ),
    )

    # ── Modo de cálculo ─────────────────────────────────────────────────────
    modo_calculo = models.CharField(
        max_length=10,
        choices=MODO_CALCULO_CHOICES,
        default='peso',
        verbose_name='Modo de cálculo',
    )

    # ── Dosis fija (puffs, inhalaciones…) ──────────────────────────────────
    dosis_fija = models.CharField(
        max_length=50, blank=True,
        verbose_name='Dosis fija',
        help_text='Ej: 2 puffs, 1 inhalación, 1 sobre. Se usa como {{DOSIS}} sin calcular por kg.',
    )

    # ── Dosificación por peso ────────────────────────────────────────────────
    unidad_dosis_kg = models.CharField(
        max_length=5,
        choices=UNIDAD_DOSIS_KG_CHOICES,
        default='mg',
        blank=True,
        verbose_name='Unidad de dosis/kg',
    )

    # ── Dosificación pediátrica (mg/kg) ────────────────────────────────────
    dosis_mg_kg_min = models.DecimalField(
        max_digits=7, decimal_places=3,
        null=True, blank=True,
        verbose_name='Dosis mínima (mg/kg/dosis)',
        help_text='Si no hay rango, usar solo este campo como dosis fija.',
    )
    dosis_mg_kg_max = models.DecimalField(
        max_digits=7, decimal_places=3,
        null=True, blank=True,
        verbose_name='Dosis máxima (mg/kg/dosis)',
        help_text='Completar solo si hay rango (leve / severo). Dejar vacío para dosis fija.',
    )
    frecuencia_horas = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Frecuencia (horas)',
        help_text='Cada cuántas horas se administra. Ej: 8 → cada 8 horas.',
    )
    duracion_dias = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Duración (días)',
        help_text='Número de días del tratamiento.',
    )

    # ── Presentación ────────────────────────────────────────────────────────
    presentacion = models.CharField(
        max_length=100, blank=True,
        verbose_name='Presentación',
        help_text='Ej: susp. 250 mg/5 mL  |  tab. 500 mg  |  gotas 100 mg/mL',
    )
    concentracion_mg = models.DecimalField(
        max_digits=8, decimal_places=3,
        null=True, blank=True,
        verbose_name='Concentración (mg)',
        help_text='mg del principio activo en la unidad de medida base.',
    )
    volumen_ml = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        verbose_name='Volumen base (mL)',
        help_text='mL correspondientes a la concentración indicada. '
                  'Ej: 5 para "250 mg/5 mL". Dejar vacío para tabletas.',
    )
    unidad_resultado = models.CharField(
        max_length=10, choices=UNIDAD_CHOICES, blank=True,
        verbose_name='Unidad del resultado',
    )

    # ── Dosificación por rango de edad ──────────────────────────────────────
    rango1_edad_min = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Rango 1 - edad mínima (meses)'
    )
    rango1_edad_max = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Rango 1 - edad máxima (meses)'
    )
    rango1_dosis = models.CharField(
        max_length=100, blank=True, verbose_name='Rango 1 - dosis',
        help_text='Ej: 1/2 sobre, 5 mL, 1 comprimido'
    )
    rango2_edad_min = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Rango 2 - edad mínima (meses)'
    )
    rango2_edad_max = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Rango 2 - edad máxima (meses)'
    )
    rango2_dosis = models.CharField(
        max_length=100, blank=True, verbose_name='Rango 2 - dosis'
    )
    rango3_edad_min = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Rango 3 - edad mínima (meses)'
    )
    rango3_edad_max = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Rango 3 - edad máxima (meses)'
    )
    rango3_dosis = models.CharField(
        max_length=100, blank=True, verbose_name='Rango 3 - dosis'
    )

    # ── Límites y alertas ───────────────────────────────────────────────────
    dosis_max_absoluta = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name='Dosis máxima absoluta (mg/dosis)',
        help_text='Techo del adulto. La dosis calculada nunca superará este valor.',
    )
    edad_min_meses = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Edad mínima (meses)',
        help_text='Se mostrará advertencia si el paciente es menor de esta edad.',
    )
    edad_max_meses = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Edad máxima (meses)',
        help_text='Alerta si el paciente supera esta edad (revisar dosis adulto).',
    )
    peso_min_kg = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name='Peso mínimo (kg)',
        help_text='Advertencia si el paciente pesa menos de este valor.',
    )

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'

    def __str__(self):
        return self.nombre

    @property
    def tiene_calculo(self):
        """True si el medicamento tiene datos suficientes para calcular/resolver dosis."""
        if self.modo_calculo == 'fija' or (self.modo_calculo == 'peso' and self.dosis_fija):
            return bool(self.dosis_fija)
        if self.modo_calculo == 'edad':
            return bool(self.rango1_dosis or self.rango2_dosis or self.rango3_dosis)
        # modo_calculo == 'peso'
        return bool(self.dosis_mg_kg_min and self.concentracion_mg and self.unidad_resultado)

    @property
    def tiene_rango(self):
        """True si la dosis tiene rango (mín/máx por kg)."""
        return bool(self.dosis_mg_kg_min and self.dosis_mg_kg_max)

    def calcular_dosis(self, peso_kg, edad_meses=None, nivel='estandar'):
        """
        Calcula la dosis para un paciente dado su peso y/o edad.
        nivel: 'minimo' | 'estandar' | 'maximo'  (solo aplica a modo peso)
        Retorna dict con texto (plantilla resuelta), alertas y valores crudos.
        """
        alertas = []
        resultado = {
            'dosis_mg': None,
            'dosis_display': None,
            'texto': self.indicaciones,
            'alertas': alertas,
            'tiene_rango': self.tiene_rango,
        }

        # ── Modo: dosis fija (puffs, inhalaciones…) ───────────────────────────
        if self.modo_calculo == 'fija' or self.dosis_fija:
            resultado['dosis_display'] = self.dosis_fija
            resultado['texto'] = self._resolver_tokens(
                peso_kg=peso_kg, dosis_mg=None, cantidad=self.dosis_fija
            )
            return resultado

        # ── Modo: por rango de edad ────────────────────────────────────────────
        if self.modo_calculo == 'edad':
            dosis_encontrada = None
            rangos = [
                (self.rango1_edad_min, self.rango1_edad_max, self.rango1_dosis),
                (self.rango2_edad_min, self.rango2_edad_max, self.rango2_dosis),
                (self.rango3_edad_min, self.rango3_edad_max, self.rango3_dosis),
            ]
            for r_min, r_max, r_dosis in rangos:
                if not r_dosis:
                    continue
                age_ok = True
                if edad_meses is not None:
                    if r_min is not None and edad_meses < r_min:
                        age_ok = False
                    if r_max is not None and edad_meses > r_max:
                        age_ok = False
                if age_ok:
                    dosis_encontrada = r_dosis
                    break
            if dosis_encontrada:
                resultado['dosis_display'] = dosis_encontrada
                resultado['texto'] = self._resolver_tokens(
                    peso_kg=peso_kg, dosis_mg=None, cantidad=dosis_encontrada
                )
            else:
                resultado['texto'] = self._resolver_tokens(
                    peso_kg=peso_kg, dosis_mg=None, cantidad='[sin rango para esta edad]'
                )
                if edad_meses is not None:
                    alertas.append({
                        'tipo': 'warning',
                        'msg': f'⚠️ No hay rango de dosis definido para {edad_meses} meses.',
                    })
            return resultado

        # ── Modo: por peso ─────────────────────────────────────────────────────
        if not self.tiene_calculo:
            # Sin datos de dosificación → devolver plantilla sin resolver
            resultado['texto'] = self._resolver_tokens(
                peso_kg=peso_kg, dosis_mg=None, cantidad=None
            )
            return resultado

        # ── Alertas de edad ────────────────────────────────────────────────
        if edad_meses is not None:
            if self.edad_min_meses and edad_meses < self.edad_min_meses:
                meses = self.edad_min_meses
                años = meses // 12
                resto = meses % 12
                txt = f'{años} años' if not resto else (
                    f'{años} años y {resto} meses' if años else f'{meses} meses'
                )
                alertas.append({
                    'tipo': 'danger',
                    'msg': f'⚠️ Contraindicado en menores de {txt}.',
                })
            if self.edad_max_meses and edad_meses > self.edad_max_meses:
                alertas.append({
                    'tipo': 'warning',
                    'msg': '⚠️ Paciente fuera del rango de edad pediátrico. Verificar dosis adulto.',
                })

        # ── Alerta de peso ─────────────────────────────────────────────────
        if self.peso_min_kg and peso_kg < float(self.peso_min_kg):
            alertas.append({
                'tipo': 'warning',
                'msg': f'⚠️ Peso por debajo del mínimo recomendado ({self.peso_min_kg} kg).',
            })

        # ── Calcular dosis en mg ───────────────────────────────────────────
        if self.tiene_rango:
            d_min = float(self.dosis_mg_kg_min)
            d_max = float(self.dosis_mg_kg_max)
            if nivel == 'minimo':
                factor = d_min
            elif nivel == 'maximo':
                factor = d_max
            else:  # estándar → punto medio
                factor = (d_min + d_max) / 2
        else:
            factor = float(self.dosis_mg_kg_min)

        dosis_mg = factor * float(peso_kg)

        # ── Aplicar techo absoluto ─────────────────────────────────────────
        if self.dosis_max_absoluta and dosis_mg > float(self.dosis_max_absoluta):
            alertas.append({
                'tipo': 'info',
                'msg': (
                    f'ℹ️ Dosis ajustada al tope máximo de '
                    f'{self.dosis_max_absoluta} mg/dosis.'
                ),
            })
            dosis_mg = float(self.dosis_max_absoluta)

        # ── Convertir a unidad de resultado ───────────────────────────────
        conc = float(self.concentracion_mg)
        if self.unidad_resultado == 'mL' and self.volumen_ml:
            cantidad = round((dosis_mg / conc) * float(self.volumen_ml), 1)
        elif self.unidad_resultado == 'tableta':
            raw = dosis_mg / conc
            # Redondear a mitades (0.5) para tabletas partibles
            cantidad = round(raw * 2) / 2
        elif self.unidad_resultado == 'gotas':
            cantidad = round((dosis_mg / conc) * float(self.volumen_ml or 1), 0)
        else:
            cantidad = round(dosis_mg, 1)

        resultado['dosis_mg'] = round(dosis_mg, 1)
        resultado['dosis_display'] = f'{cantidad} {self.unidad_resultado}'

        resultado['texto'] = self._resolver_tokens(
            peso_kg=peso_kg,
            dosis_mg=round(dosis_mg, 1),
            cantidad=cantidad,
        )
        return resultado

    def _resolver_tokens(self, peso_kg, dosis_mg, cantidad):
        """Reemplaza los tokens de la plantilla con valores reales."""
        frecuencia_txt = (
            f'cada {self.frecuencia_horas} horas' if self.frecuencia_horas else ''
        )
        duracion_txt = (
            f'por {self.duracion_dias} día{"s" if self.duracion_dias != 1 else ""}'
            if self.duracion_dias else ''
        )
        # {{DOSIS}} — cantidad en unidad de resultado (mL, tableta, puff…)
        if cantidad is not None and self.unidad_resultado and self.modo_calculo == 'peso':
            dosis_txt = f'{cantidad} {self.unidad_resultado}'
        elif cantidad is not None:
            # edad o fija mode: cantidad ya es el string completo
            dosis_txt = str(cantidad)
        else:
            dosis_txt = ''
        # {{DOSIS_MG}} — dosis en la unidad por kg (mg, mcg, UI, g)
        unidad_kg = self.unidad_dosis_kg or 'mg'
        dosis_mg_txt = f'{dosis_mg} {unidad_kg}' if dosis_mg is not None else ''
        reemplazos = {
            '{{NOMBRE}}':       self.nombre,
            '{{PRESENTACION}}': self.presentacion or '',
            '{{DOSIS}}':        dosis_txt,
            '{{DOSIS_MG}}':     dosis_mg_txt,
            '{{FRECUENCIA}}':   frecuencia_txt,
            '{{DURACION}}':     duracion_txt,
            '{{PESO}}':         f'{peso_kg} kg' if peso_kg is not None else '',
        }
        texto = self.indicaciones
        for token, valor in reemplazos.items():
            texto = texto.replace(token, valor)
        return texto
