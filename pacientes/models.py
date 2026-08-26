from django.db import models
from django.core.validators import RegexValidator


cedula_validator = RegexValidator(
    regex=r'^[VvEe]-\d{6,9}$',
    message='La cédula debe tener formato V-xxxxxxxx o E-xxxxxxxx'
)

cedula_representante_validator = RegexValidator(
    regex=r'^[VvEe]-\d{6,9}-\d+$',
    message='La cédula del representante debe tener formato V-xxxxxxxx-N (ej: V-12345678-1)'
)


class Paciente(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    ESTADO_CIVIL_CHOICES = [
        ('soltero', 'Soltero/a'),
        ('casado', 'Casado/a'),
        ('union_libre', 'Unión libre'),
        ('divorciado', 'Divorciado/a'),
        ('viudo', 'Viudo/a'),
    ]
    INSTRUCCION_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('tecnico', 'Técnico'),
        ('universitario', 'Universitario'),
        ('postgrado', 'Postgrado'),
    ]
    GRUPO_SANGUINEO_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    FILIACION_CHOICES = [
        ('madre', 'Madre'),
        ('padre', 'Padre'),
        ('otro', 'Otro'),
    ]
    VIA_PARTO_CHOICES = [
        ('vaginal', 'Vaginal'),
        ('cesarea', 'Cesárea'),
    ]
    ONFALORREXIS_CHOICES = [
        ('normal', 'Normal / Sin complicaciones'),
        ('complicada', 'Alterada / Complicada'),
    ]
    PRUEBA_TALON_CHOICES = [
        ('normal', 'Sin alteraciones (Normal)'),
        ('alterada', 'Alterada / En estudio'),
    ]
    CAUSA_FORMULA_CHOICES = [
        ('evacuaciones', 'Dificultad en evacuaciones'),
        ('estimulacion', 'Necesidad de estimulación'),
        ('alergia', 'Alergia'),
        ('otra', 'Otra'),
    ]
    ALIMENTACION_ACTUAL_CHOICES = [
        ('completa', 'Dieta completa y variada acorde a la edad'),
        ('selectiva', 'Dieta selectiva / Restringida'),
    ]
    ANTEC_ONCOLOGICO_RAMA_CHOICES = [
        ('materna', 'Materna'),
        ('paterna', 'Paterna'),
        ('ambas', 'Ambas'),
    ]
    PATRON_SUENO_CHOICES = [
        ('tranquilo', 'Tranquilo, reparador y conservado'),
        ('alterado', 'Alterado / Trastorno del sueño'),
    ]
    PATRON_EVACUACION_CHOICES = [
        ('normal', 'Normal / Continente'),
        ('estrenimiento', 'Estreñimiento'),
        ('encopresis', 'Encopresis (incontinencia fecal)'),
    ]
    PATRON_MICCION_CHOICES = [
        ('normal', 'Normal / Continente'),
        ('enuresis_diurna', 'Enuresis diurna'),
        ('enuresis_nocturna', 'Enuresis nocturna'),
    ]
    AGUA_CONSUMO_CHOICES = [
        ('hervida', 'Hervida'),
        ('filtrada', 'Filtrada'),
        ('embotellada', 'Embotellada'),
        ('tuberia', 'Directa de tubería'),
    ]

    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='pacientes',
        verbose_name='Consultorio',
    )

    # ── Datos personales ────────────────────────────────────────────────────
    nombre_completo = models.CharField(max_length=200, verbose_name='Nombre completo')
    sexo = models.CharField(
        max_length=1, choices=SEXO_CHOICES, blank=True, verbose_name='Sexo biológico'
    )
    no_cedulado = models.BooleanField(
        default=False,
        verbose_name='Paciente no cedulado',
        help_text='Marcar si el paciente aún no tiene cédula (niño/a sin cédula)'
    )
    cedula = models.CharField(
        max_length=15,
        validators=[cedula_validator],
        verbose_name='Cédula del paciente',
        help_text='Formato: V-12345678 o E-12345678',
        blank=True,
        default='',
    )
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    telefono = models.CharField(max_length=20, blank=True, default='', verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email')
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    seguro_medico = models.CharField(max_length=100, blank=True, verbose_name='Seguro médico')

    # ── Datos del representante / padres ────────────────────────────────────
    nombre_padre = models.CharField(max_length=200, blank=True, verbose_name='Nombre del padre')
    nombre_madre = models.CharField(max_length=200, blank=True, verbose_name='Nombre de la madre')
    nombre_representante = models.CharField(max_length=200, blank=True, verbose_name='Nombre del representante')
    filiacion_representante = models.CharField(
        max_length=10, choices=FILIACION_CHOICES, blank=True,
        verbose_name='Filiación del representante',
    )
    parentesco_representante = models.CharField(
        max_length=100, blank=True,
        verbose_name='Parentesco (si es otro)',
        help_text='Ej: abuela, tío, tutor legal',
    )
    cedula_representante = models.CharField(
        max_length=20, blank=True,
        validators=[cedula_representante_validator],
        verbose_name='Cédula del representante',
        help_text='Formato: V-12345678-1'
    )
    telefono_representante = models.CharField(
        max_length=20, blank=True, verbose_name='Teléfono del representante'
    )
    ocupacion_representante = models.CharField(
        max_length=100, blank=True, verbose_name='Ocupación del representante'
    )
    contacto_emergencia = models.CharField(
        max_length=200, blank=True, verbose_name='Contacto de emergencia'
    )
    # Datos adicionales de los padres
    edad_madre = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Edad de la madre (años)'
    )
    ocupacion_madre = models.CharField(
        max_length=100, blank=True, verbose_name='Ocupación de la madre'
    )
    edad_padre = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Edad del padre (años)'
    )
    ocupacion_padre = models.CharField(
        max_length=100, blank=True, verbose_name='Ocupación del padre'
    )

    # ── Antecedentes personales ─────────────────────────────────────────────
    alergias = models.TextField(blank=True, verbose_name='Alergias')
    enfermedades_cronicas = models.TextField(blank=True, verbose_name='Enfermedades crónicas')
    cirugias_previas = models.TextField(blank=True, verbose_name='Cirugías y hospitalizaciones previas')
    medicacion_actual = models.TextField(blank=True, verbose_name='Medicación actual')
    grupo_sanguineo = models.CharField(
        max_length=5, choices=GRUPO_SANGUINEO_CHOICES,
        blank=True, verbose_name='Grupo sanguíneo'
    )

    # ── Antecedentes perinatales (texto libre legacy) ──────────────────────
    antec_embarazo = models.TextField(
        blank=True, verbose_name='Antecedentes del embarazo',
        help_text='Patologías maternas, control prenatal, exposición a riesgos'
    )
    peso_nacer = models.DecimalField(
        max_digits=4, decimal_places=0,
        null=True, blank=True,
        verbose_name='Peso al nacer (g)',
        help_text='En gramos. Ej: 3200'
    )
    talla_nacer = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        verbose_name='Talla al nacer (cm)',
        help_text='En centímetros. Ej: 50.5'
    )
    antec_parto = models.TextField(
        blank=True, verbose_name='Antecedentes del parto / nacimiento',
        help_text='Vía de parto, edad gestacional, APGAR'
    )
    antec_neonatal = models.TextField(
        blank=True, verbose_name='Período neonatal',
        help_text='Estadía en retén, ictericia, lactancia, tamiz neonatal'
    )

    # ── Antecedentes perinatales (estructurado) ─────────────────────────────
    edad_materna_embarazo = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Edad materna al embarazo (años)'
    )
    numero_gestacion = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='N° de gestación',
        help_text='Ej: 1 = primera gestación'
    )
    control_prenatal = models.BooleanField(
        null=True, blank=True, verbose_name='Control prenatal'
    )
    num_consultas_prenatales = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='N° de consultas prenatales'
    )
    complicacion_oligoamnios = models.BooleanField(
        default=False, verbose_name='Oligoamnios'
    )
    complicacion_preeclampsia = models.BooleanField(
        default=False, verbose_name='Preeclampsia'
    )
    complicacion_infecciones = models.BooleanField(
        default=False, verbose_name='Infecciones durante embarazo'
    )
    complicacion_embarazo_otra = models.CharField(
        max_length=200, blank=True, verbose_name='Otra complicación en el embarazo'
    )
    semanas_gestacion = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Semanas de gestación al nacer'
    )
    via_parto = models.CharField(
        max_length=10, choices=VIA_PARTO_CHOICES,
        blank=True, verbose_name='Vía de resolución del parto'
    )
    indicacion_cesarea = models.CharField(
        max_length=200, blank=True, verbose_name='Indicación de cesárea'
    )
    complicaciones_neonatales = models.BooleanField(
        null=True, blank=True, verbose_name='Presentó complicaciones neonatales'
    )
    neonatal_ictericia = models.BooleanField(default=False, verbose_name='Ictericia neonatal')
    neonatal_sepsis = models.BooleanField(default=False, verbose_name='Sepsis neonatal')
    neonatal_dificultad_respiratoria = models.BooleanField(
        default=False, verbose_name='Dificultad respiratoria neonatal'
    )
    neonatal_otra_complicacion = models.CharField(
        max_length=200, blank=True, verbose_name='Otra complicación neonatal'
    )
    onfalorrexis = models.CharField(
        max_length=12, choices=ONFALORREXIS_CHOICES,
        blank=True, verbose_name='Onfalorrexis (caída del cordón umbilical)'
    )
    prueba_talon = models.CharField(
        max_length=10, choices=PRUEBA_TALON_CHOICES,
        blank=True, verbose_name='Prueba del talón'
    )
    prueba_talon_detalle = models.CharField(
        max_length=300, blank=True, verbose_name='Detalle prueba del talón alterada'
    )

    # ── Antecedentes familiares ─────────────────────────────────────────────
    antec_diabetes = models.BooleanField(default=False, verbose_name='Antec. familiar diabetes')
    antec_hipertension = models.BooleanField(default=False, verbose_name='Antec. familiar hipertensión')
    antec_cardiopatias = models.BooleanField(default=False, verbose_name='Antec. familiar cardiopatías')
    antec_epilepsia = models.BooleanField(default=False, verbose_name='Antec. familiar epilepsia')
    antec_asma_atopia = models.BooleanField(default=False, verbose_name='Antec. familiar asma / atopía')
    antec_autoinmunes = models.TextField(blank=True, verbose_name='Antec. familiar enfermedades autoinmunes')
    antec_geneticas = models.TextField(blank=True, verbose_name='Antec. familiar enfermedades genéticas')
    antec_otros = models.TextField(blank=True, verbose_name='Otros antecedentes familiares')

    # ── Antecedentes de alimentación y desarrollo ───────────────────────────
    antec_alimentacion = models.TextField(
        blank=True, verbose_name='Antecedentes de alimentación',
        help_text='Lactancia materna/fórmula, ablactación, dieta actual, alergias alimentarias'
    )
    antec_desarrollo = models.TextField(
        blank=True, verbose_name='Desarrollo psicomotor',
        help_text='Hitos del desarrollo: sostén cefálico, sedestación, marcha, lenguaje, control de esfínteres'
    )

    # ── Alimentación (estructurado) ─────────────────────────────────────────
    lme = models.BooleanField(
        null=True, blank=True, verbose_name='Lactancia materna exclusiva (LME)'
    )
    lme_meses = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='LME hasta (meses)'
    )
    uso_formula = models.BooleanField(
        null=True, blank=True, verbose_name='Uso de fórmulas o leches especiales'
    )
    nombre_formula = models.CharField(
        max_length=100, blank=True, verbose_name='Nombre de fórmula empleada'
    )
    causa_formula = models.CharField(
        max_length=15, choices=CAUSA_FORMULA_CHOICES,
        blank=True, verbose_name='Causa del uso de fórmula'
    )
    alimentacion_actual = models.CharField(
        max_length=10, choices=ALIMENTACION_ACTUAL_CHOICES,
        blank=True, verbose_name='Alimentación actual'
    )
    alimentacion_actual_detalle = models.CharField(
        max_length=300, blank=True,
        verbose_name='Detalle dieta selectiva/restringida'
    )

    # ── Desarrollo psicomotor (estructurado) ────────────────────────────────
    desarrollo_psicomotor_adecuado = models.BooleanField(
        null=True, blank=True,
        verbose_name='Desarrollo neuromotor acorde a la edad'
    )
    desarrollo_area_afectada = models.CharField(
        max_length=100, blank=True,
        verbose_name='Área de desarrollo afectada',
        help_text='Ej: Motor grueso, Motor fino, Lenguaje, Social-afectivo'
    )
    esfinter_vesical_logrado = models.BooleanField(
        null=True, blank=True, verbose_name='Control esfínter vesical (micción) logrado'
    )
    esfinter_vesical_edad = models.CharField(
        max_length=30, blank=True, verbose_name='Edad logro control vesical'
    )
    esfinter_anal_logrado = models.BooleanField(
        null=True, blank=True, verbose_name='Control esfínter anal (evacuación) logrado'
    )
    esfinter_anal_edad = models.CharField(
        max_length=30, blank=True, verbose_name='Edad logro control anal'
    )

    # ── Antecedentes patológicos (estructurado adicional) ───────────────────
    traumatismos = models.BooleanField(
        null=True, blank=True, verbose_name='Traumatismos / Accidentes'
    )
    traumatismos_detalle = models.CharField(
        max_length=300, blank=True, verbose_name='Detalle de traumatismos'
    )
    enfermedades_exantematicas = models.BooleanField(
        null=True, blank=True, verbose_name='Enfermedades exantemáticas'
    )
    exantematicas_detalle = models.CharField(
        max_length=200, blank=True,
        verbose_name='Detalle enfermedades exantemáticas',
        help_text='Varicela, Sarampión, Rubéola, etc.'
    )

    # ── Antecedentes familiares (adicional) ─────────────────────────────────
    antec_oncologico = models.BooleanField(
        default=False, verbose_name='Antec. familiar patología oncológica'
    )
    antec_oncologico_rama = models.CharField(
        max_length=8, choices=ANTEC_ONCOLOGICO_RAMA_CHOICES,
        blank=True, verbose_name='Rama familiar oncológica'
    )

    # ── Hábitos psicobiológicos y entorno ───────────────────────────────────
    patron_sueno = models.CharField(
        max_length=10, choices=PATRON_SUENO_CHOICES,
        blank=True, verbose_name='Patrón de sueño'
    )
    patron_evacuacion = models.CharField(
        max_length=15, choices=PATRON_EVACUACION_CHOICES,
        blank=True, verbose_name='Patrón de evacuación'
    )
    patron_miccion = models.CharField(
        max_length=18, choices=PATRON_MICCION_CHOICES,
        blank=True, verbose_name='Patrón de micción'
    )
    tabaquismo_pasivo = models.BooleanField(
        null=True, blank=True, verbose_name='Exposición a humo de tabaco (tabaquismo pasivo)'
    )
    agua_consumo = models.CharField(
        max_length=12, choices=AGUA_CONSUMO_CHOICES,
        blank=True, verbose_name='Tratamiento del agua de consumo'
    )
    mascotas = models.BooleanField(
        null=True, blank=True, verbose_name='Mascotas en el hogar'
    )
    mascotas_tipo = models.CharField(
        max_length=100, blank=True, verbose_name='Tipo de mascotas'
    )

    # ── Observaciones ───────────────────────────────────────────────────────
    observaciones = models.TextField(blank=True, verbose_name='Observaciones generales')

    # ── Control ─────────────────────────────────────────────────────────────
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nombre_completo']

    def __str__(self):
        if self.no_cedulado:
            return f'{self.nombre_completo} (S/C - Rep: {self.cedula_representante})'
        return f'{self.nombre_completo} ({self.cedula})'

    def get_edad(self):
        if not self.fecha_nacimiento:
            return '—'
        from datetime import date
        hoy = date.today()
        return (
            hoy.year - self.fecha_nacimiento.year
            - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        )

    def get_edad_detallada(self):
        """Retorna edad en años, meses y días."""
        if not self.fecha_nacimiento:
            return '—'
        from datetime import date
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(date.today(), self.fecha_nacimiento)
        if delta.years >= 2:
            return f'{delta.years} años'
        elif delta.years == 1:
            return f'1 año y {delta.months} meses'
        elif delta.months > 0:
            return f'{delta.months} meses y {delta.days} días'
        else:
            return f'{delta.days} días'

    def get_edad_en_meses(self):
        """Retorna la edad actual en meses (para calcular vacunas pendientes)."""
        if not self.fecha_nacimiento:
            return None
        from datetime import date
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(date.today(), self.fecha_nacimiento)
        return delta.years * 12 + delta.months

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.no_cedulado:
            self.cedula = ''
            if not self.cedula_representante:
                raise ValidationError({'cedula_representante': 'Debe ingresar la cédula del representante para pacientes no cedulados.'})
            qs = Paciente.objects.filter(
                tenant=self.tenant,
                cedula_representante=self.cedula_representante,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'cedula_representante': 'Ya existe un paciente registrado con esta cédula de representante en este consultorio.'})
        else:
            # Cédula es opcional — solo validar unicidad si se proporcionó
            if self.cedula:
                qs = Paciente.objects.filter(
                    tenant=self.tenant,
                    cedula=self.cedula,
                )
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                if qs.exists():
                    raise ValidationError({'cedula': 'Ya existe un paciente registrado con esta cédula en este consultorio.'})

    @staticmethod
    def _limpiar_telefono(valor):
        """Elimina todo carácter no numérico excepto + (quita invisibles Unicode, espacios, guiones, etc.)."""
        import re
        return re.sub(r'[^\d+]', '', valor or '')

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            raise ValueError('Un paciente no puede guardarse sin tenant.')
        self.telefono = self._limpiar_telefono(self.telefono)
        self.telefono_representante = self._limpiar_telefono(self.telefono_representante)
        super().save(*args, **kwargs)


# ── Catálogo de vacunas ───────────────────────────────────────────────────────

class Vacuna(models.Model):
    """Catálogo de vacunas — base PAI Venezuela + vacunas adicionales por tenant."""
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='vacunas_extra',
        verbose_name='Consultorio',
        help_text='Null = vacuna PAI (compartida). Con tenant = vacuna adicional del consultorio.',
    )
    nombre = models.CharField(max_length=100, verbose_name='Vacuna')
    enfermedad = models.CharField(max_length=200, blank=True, verbose_name='Protege contra')
    dosis_numero = models.PositiveSmallIntegerField(verbose_name='N° dosis')
    edad_recomendada_meses = models.PositiveSmallIntegerField(
        verbose_name='Edad recomendada (meses)',
        help_text='0 = al nacer, 2 = 2 meses, 12 = 1 año, etc.'
    )
    edad_max_meses = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Edad máxima (meses)',
        help_text='Si se supera esta edad se marca como atrasada.',
    )
    es_pai = models.BooleanField(default=True, verbose_name='Vacuna PAI (esquema oficial)')
    activa = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Vacuna'
        verbose_name_plural = 'Vacunas'
        ordering = ['orden', 'edad_recomendada_meses', 'dosis_numero']

    def __str__(self):
        return f'{self.nombre} (dosis {self.dosis_numero}) — {self.edad_recomendada_meses}m'

    def edad_display(self):
        m = self.edad_recomendada_meses
        if m == 0:
            return 'Al nacer'
        if m < 12:
            return f'{m} meses'
        if m % 12 == 0:
            return f'{m // 12} año{"s" if m // 12 > 1 else ""}'
        return f'{m // 12} año{"s" if m // 12 > 1 else ""} y {m % 12} m'


class VacunaAplicada(models.Model):
    """Registro de una dosis aplicada a un paciente."""
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='vacunas_aplicadas',
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='vacunas_aplicadas',
    )
    vacuna = models.ForeignKey(
        Vacuna,
        on_delete=models.PROTECT,
        related_name='aplicaciones',
    )
    fecha = models.DateField(verbose_name='Fecha de aplicación')
    lote = models.CharField(max_length=50, blank=True, verbose_name='Lote / Laboratorio')
    observaciones = models.CharField(max_length=300, blank=True, verbose_name='Observaciones')
    aplicada_por = models.ForeignKey(
        'accounts.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vacunas_aplicadas',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vacuna aplicada'
        verbose_name_plural = 'Vacunas aplicadas'
        ordering = ['fecha']
        unique_together = [['paciente', 'vacuna']]

    def __str__(self):
        return f'{self.paciente} — {self.vacuna.nombre} d{self.vacuna.dosis_numero} ({self.fecha})'
