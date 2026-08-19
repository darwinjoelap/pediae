from django.contrib import admin
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'cedula', 'get_edad', 'telefono', 'get_formula_obstetrica', 'creado_en')
    list_filter = ('estado_civil', 'nivel_instruccion', 'menopausia', 'tabaquismo')
    search_fields = ('nombre_completo', 'cedula', 'telefono')
    readonly_fields = ('creado_en', 'actualizado_en')
    fieldsets = (
        ('Datos personales', {
            'fields': (
                'nombre_completo', 'cedula', 'fecha_nacimiento', 'telefono',
                'estado_civil', 'nivel_instruccion', 'ocupacion',
                'direccion', 'contacto_emergencia', 'seguro_medico',
            )
        }),
        ('Antecedentes personales', {
            'fields': (
                'alergias', 'enfermedades_cronicas', 'cirugias_previas',
                'medicacion_actual', 'tabaquismo', 'alcoholismo',
                'grupo_sanguineo', 'transfusiones',
            ),
            'classes': ('collapse',),
        }),
        ('Antecedentes familiares', {
            'fields': (
                'antec_cancer_mama', 'antec_cancer_cuello',
                'antec_diabetes', 'antec_hipertension',
                'antec_autoinmunes', 'antec_geneticas',
            ),
            'classes': ('collapse',),
        }),
        ('Historia gineco-obstétrica', {
            'fields': (
                'menarquia', 'ciclo_dias', 'ciclo_regular', 'fur',
                'gestas', 'partos', 'cesareas', 'abortos', 'fecha_ultimo_parto',
                'ultima_citologia_fecha', 'ultima_citologia_resultado',
                'vph_diagnostico', 'vph_vacuna',
                'vih_resultado', 'vih_fecha', 'its_previas',
                'inicio_vida_sexual', 'num_parejas', 'dispareunia',
                'menopausia', 'menopausia_edad', 'menopausia_sintomas',
            ),
            'classes': ('collapse',),
        }),
        ('Planificación familiar', {
            'fields': (
                'metodo_anticonceptivo', 'metodo_tiempo_uso', 'metodos_anteriores',
                'deseo_embarazo', 'diu_fecha', 'diu_tipo', 'ligadura',
            ),
            'classes': ('collapse',),
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
        }),
        ('Control', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',),
        }),
    )

    def get_edad(self, obj):
        return f'{obj.get_edad()} años'
    get_edad.short_description = 'Edad'

    def get_formula_obstetrica(self, obj):
        return obj.get_formula_obstetrica()
    get_formula_obstetrica.short_description = 'Fórmula obstétrica'
