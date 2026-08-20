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
    ESTADO_CIVIL_CHOICES = [
        ('soltera', 'Soltera'),
        ('casada', 'Casada'),
        ('union_libre', 'Unión libre'),
        ('divorciada', 'Divorciada'),
        ('viuda', 'Viuda'),
    ]
    INSTRUCCION_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('tecnico', 'Técnico'),
        ('universitario', 'Universitario'),
        ('postgrado', 'Postgrado'),
    ]
    VIH_CHOICES = [
        ('negativo', 'Negativo'),
        ('positivo', 'Positivo'),
        ('no_realizado', 'No realizado'),
    ]
    GRUPO_SANGUINEO_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='pacientes',
        verbose_name='Consultorio',
    )

    # Datos personales
    nombre_completo = models.CharField(max_length=200, verbose_name='Nombre completo')
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
    # Datos del representante
    FILIACION_CHOICES = [
        ('madre', 'Madre'),
        ('padre', 'Padre'),
        ('otro', 'Otro'),
    ]
    nombre_padre = models.CharField(max_length=200, blank=True, verbose_name='Nombre del padre')
    nombre_madre = models.CharField(max_length=200, blank=True, verbose_name='Nombre de la madre')
    nombre_representante = models.CharField(max_length=200, blank=True, verbose_name='Nombre del representante')
    filiacion_representante = models.CharField(
        max_length=10,
        choices=FILIACION_CHOICES,
        blank=True,
        verbose_name='Filiación del representante',
    )
    parentesco_representante = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Parentesco (si es otro)',
        help_text='Ej: abuela, tío, tutor legal',
    )
    cedula_representante = models.CharField(
        max_length=20,
        blank=True,
        validators=[cedula_representante_validator],
        verbose_name='Cédula del representante',
        help_text='Formato: V-12345678-1 (el número final identifica al hijo/representado)'
    )
    fecha_nacimiento = models.DateField(
        null=True, blank=True,
        verbose_name='Fecha de nacimiento'
    )
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email',
        help_text='Opcional — se usará para recordatorios por correo')
    estado_civil = models.CharField(
        max_length=20, choices=ESTADO_CIVIL_CHOICES,
        blank=True, verbose_name='Estado civil'
    )
    nivel_instruccion = models.CharField(
        max_length=20, choices=INSTRUCCION_CHOICES,
        blank=True, verbose_name='Nivel de instrucción'
    )
    ocupacion = models.CharField(max_length=100, blank=True, verbose_name='Ocupación')
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    contacto_emergencia = models.CharField(max_length=200, blank=True, verbose_name='Contacto de emergencia')
    seguro_medico = models.CharField(max_length=100, blank=True, verbose_name='Seguro médico')

    # Antecedentes personales
    alergias = models.TextField(blank=True, verbose_name='Alergias')
    enfermedades_cronicas = models.TextField(blank=True, verbose_name='Enfermedades crónicas')
    cirugias_previas = models.TextField(blank=True, verbose_name='Cirugías previas')
    medicacion_actual = models.TextField(blank=True, verbose_name='Medicación actual')
    tabaquismo = models.BooleanField(default=False, verbose_name='Tabaquismo')
    alcoholismo = models.BooleanField(default=False, verbose_name='Alcoholismo')
    grupo_sanguineo = models.CharField(
        max_length=5, choices=GRUPO_SANGUINEO_CHOICES,
        blank=True, verbose_name='Grupo sanguíneo'
    )
    transfusiones = models.BooleanField(default=False, verbose_name='Transfusiones')

    # Antecedentes familiares
    antec_cancer_mama = models.BooleanField(default=False, verbose_name='Antec. familiar cáncer de mama')
    antec_cancer_cuello = models.BooleanField(default=False, verbose_name='Antec. familiar cáncer de cuello uterino')
    antec_diabetes = models.BooleanField(default=False, verbose_name='Antec. familiar diabetes')
    antec_hipertension = models.BooleanField(default=False, verbose_name='Antec. familiar hipertensión')
    antec_autoinmunes = models.TextField(blank=True, verbose_name='Antec. familiar enfermedades autoinmunes')
    antec_geneticas = models.TextField(blank=True, verbose_name='Antec. familiar enfermedades genéticas')
    antec_otros = models.TextField(blank=True, verbose_name='Otros antecedentes familiares')

    # Historia gineco-obstétrica
    menarquia = models.IntegerField(null=True, blank=True, verbose_name='Menarquía (edad)')
    ciclo_dias = models.IntegerField(null=True, blank=True, verbose_name='Duración del ciclo (días)')
    ciclo_regular = models.BooleanField(default=True, verbose_name='Ciclo regular')
    ciclo_caracteristicas = models.TextField(blank=True, verbose_name='Características del sangrado menstrual')
    fur = models.DateField(null=True, blank=True, verbose_name='FUR (Fecha última regla)')
    gestas = models.IntegerField(default=0, verbose_name='Gestas')
    partos = models.IntegerField(default=0, verbose_name='Partos')
    cesareas = models.IntegerField(default=0, verbose_name='Cesáreas')
    abortos = models.IntegerField(default=0, verbose_name='Abortos')
    fecha_ultimo_parto = models.DateField(null=True, blank=True, verbose_name='Fecha último parto')
    ultima_citologia_fecha = models.DateField(null=True, blank=True, verbose_name='Última citología (fecha)')
    ultima_citologia_resultado = models.CharField(max_length=100, blank=True, verbose_name='Última citología (resultado)')
    ultima_citologia_hace = models.CharField(
        max_length=100, blank=True,
        verbose_name='Última citología (tiempo aproximado)',
        help_text='Ej: "hace 2 años", "hace 6 meses"'
    )
    vph_diagnostico = models.BooleanField(default=False, verbose_name='Diagnóstico VPH')
    vph_vacuna = models.BooleanField(default=False, verbose_name='Vacuna VPH')
    vih_resultado = models.CharField(max_length=20, choices=VIH_CHOICES, default='no_realizado', verbose_name='Resultado VIH')
    vih_fecha = models.DateField(null=True, blank=True, verbose_name='VIH (fecha prueba)')
    its_previas = models.TextField(blank=True, verbose_name='ITS previas')
    inicio_vida_sexual = models.IntegerField(null=True, blank=True, verbose_name='Inicio vida sexual (edad)')
    num_parejas = models.IntegerField(null=True, blank=True, verbose_name='Número de parejas sexuales')
    dispareunia = models.BooleanField(default=False, verbose_name='Dispareunia')
    menopausia = models.BooleanField(default=False, verbose_name='Menopausia')
    menopausia_edad = models.IntegerField(null=True, blank=True, verbose_name='Menopausia (edad)')
    menopausia_sintomas = models.TextField(blank=True, verbose_name='Síntomas de menopausia')

    # Planificación familiar
    metodo_anticonceptivo = models.CharField(max_length=100, blank=True, verbose_name='Método anticonceptivo actual')
    metodo_tiempo_uso = models.CharField(max_length=100, blank=True, verbose_name='Tiempo de uso del método')
    metodos_anteriores = models.TextField(blank=True, verbose_name='Métodos anticonceptivos anteriores')
    deseo_embarazo = models.BooleanField(default=False, verbose_name='Deseo de embarazo')
    diu_fecha = models.DateField(null=True, blank=True, verbose_name='DIU (fecha de colocación)')
    diu_tipo = models.CharField(max_length=100, blank=True, verbose_name='Tipo de DIU')
    ligadura = models.BooleanField(default=False, verbose_name='Ligadura de trompas')

    # Observaciones
    observaciones = models.TextField(blank=True, verbose_name='Observaciones generales')

    # Control
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nombre_completo']
        unique_together = [['tenant', 'cedula']]

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

    def get_formula_obstetrica(self):
        return f'G{self.gestas} P{self.partos} C{self.cesareas} A{self.abortos}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.no_cedulado:
            self.cedula = ''
            if not self.cedula_representante:
                raise ValidationError({'cedula_representante': 'Debe ingresar la cédula del representante para pacientes no cedulados.'})
        else:
            if not self.cedula:
                raise ValidationError({'cedula': 'La cédula es obligatoria para pacientes cedulados.'})

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            raise ValueError('Un paciente no puede guardarse sin tenant.')
        super().save(*args, **kwargs)
