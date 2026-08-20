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
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
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

    # ── Antecedentes personales ─────────────────────────────────────────────
    alergias = models.TextField(blank=True, verbose_name='Alergias')
    enfermedades_cronicas = models.TextField(blank=True, verbose_name='Enfermedades crónicas')
    cirugias_previas = models.TextField(blank=True, verbose_name='Cirugías y hospitalizaciones previas')
    medicacion_actual = models.TextField(blank=True, verbose_name='Medicación actual')
    grupo_sanguineo = models.CharField(
        max_length=5, choices=GRUPO_SANGUINEO_CHOICES,
        blank=True, verbose_name='Grupo sanguíneo'
    )

    # ── Antecedentes perinatales (texto libre) ──────────────────────────────
    antec_embarazo = models.TextField(
        blank=True, verbose_name='Antecedentes del embarazo',
        help_text='Patologías maternas, control prenatal, exposición a riesgos'
    )
    antec_parto = models.TextField(
        blank=True, verbose_name='Antecedentes del parto / nacimiento',
        help_text='Vía de parto, edad gestacional, APGAR, peso y talla al nacer'
    )
    antec_neonatal = models.TextField(
        blank=True, verbose_name='Período neonatal',
        help_text='Estadía en retén, ictericia, lactancia, tamiz neonatal'
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
            if not self.cedula:
                raise ValidationError({'cedula': 'La cédula es obligatoria para pacientes cedulados.'})
            qs = Paciente.objects.filter(
                tenant=self.tenant,
                cedula=self.cedula,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'cedula': 'Ya existe un paciente registrado con esta cédula en este consultorio.'})

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            raise ValueError('Un paciente no puede guardarse sin tenant.')
        super().save(*args, **kwargs)
