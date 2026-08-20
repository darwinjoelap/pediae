from django.contrib import admin
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'cedula', 'get_edad_detallada', 'sexo', 'telefono', 'creado_en')
    list_filter = ('sexo', 'no_cedulado', 'antec_diabetes', 'antec_hipertension')
    search_fields = ('nombre_completo', 'cedula', 'cedula_representante', 'telefono')
    readonly_fields = ('creado_en', 'actualizado_en')
    fieldsets = (
        ('Datos personales', {
            'fields': (
                'nombre_completo', 'sexo', 'no_cedulado', 'cedula',
                'fecha_nacimiento', 'telefono', 'email',
                'direccion', 'contacto_emergencia', 'seguro_medico',
            )
        }),
        ('Representante / Padres', {
            'fields': (
                'filiacion_representante', 'nombre_representante',
                'cedula_representante', 'parentesco_representante',
                'nombre_padre', 'nombre_madre',
                'telefono_representante', 'ocupacion_representante',
            ),
            'classes': ('collapse',),
        }),
        ('Antecedentes personales', {
            'fields': (
                'alergias', 'enfermedades_cronicas', 'cirugias_previas',
                'medicacion_actual', 'grupo_sanguineo',
            ),
            'classes': ('collapse',),
        }),
        ('Antecedentes perinatales', {
            'fields': ('antec_embarazo', 'antec_parto', 'antec_neonatal'),
            'classes': ('collapse',),
        }),
        ('Antecedentes familiares', {
            'fields': (
                'antec_diabetes', 'antec_hipertension',
                'antec_cardiopatias', 'antec_epilepsia', 'antec_asma_atopia',
                'antec_autoinmunes', 'antec_geneticas', 'antec_otros',
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

    def get_edad_detallada(self, obj):
        return obj.get_edad_detallada()
    get_edad_detallada.short_description = 'Edad'
