from django.contrib import admin
from .models import Consulta, AdjuntoConsulta


class AdjuntoInline(admin.TabularInline):
    model = AdjuntoConsulta
    extra = 0
    readonly_fields = ('subido_en', 'get_url_display')
    fields = ('nombre_original', 'tipo', 'drive_file_id', 'get_url_display', 'subido_en')

    def get_url_display(self, obj):
        if obj.pk:
            from django.utils.html import format_html
            return format_html('<a href="{}" target="_blank">Ver</a>', obj.get_url())
        return '—'
    get_url_display.short_description = 'Enlace'


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha', 'tipo_consulta', 'diagnostico', 'clasificacion_nutricional', 'creado_en')
    list_filter = ('tipo_consulta', 'clasificacion_nutricional', 'fecha')
    search_fields = ('paciente__nombre_completo', 'paciente__cedula', 'diagnostico')
    date_hierarchy = 'fecha'
    readonly_fields = ('creado_en', 'percentil_peso', 'percentil_talla', 'percentil_pc', 'clasificacion_nutricional')
    inlines = [AdjuntoInline]
    fieldsets = (
        ('Datos básicos', {
            'fields': ('paciente', 'cita', 'fecha', 'tipo_consulta', 'lugar', 'medico')
        }),
        ('Antropometría y signos vitales', {
            'fields': (
                'peso', 'talla', 'perimetro_cefalico',
                'frecuencia_cardiaca', 'frecuencia_respiratoria',
                'temperatura', 'saturacion_oxigeno', 'tension_arterial',
                'percentil_peso', 'percentil_talla', 'percentil_pc',
                'clasificacion_nutricional',
            )
        }),
        ('Clínica', {
            'fields': ('motivo_consulta', 'sintomas_actuales', 'examen_fisico',
                       'desarrollo_psicomotor', 'diagnostico', 'tratamiento',
                       'laboratorio', 'proxima_cita', 'observaciones')
        }),
        ('Pago', {
            'fields': ('pagado', 'notas_pago'),
            'classes': ('collapse',),
        }),
        ('Control', {
            'fields': ('creado_en',),
            'classes': ('collapse',),
        }),
    )


@admin.register(AdjuntoConsulta)
class AdjuntoConsultaAdmin(admin.ModelAdmin):
    list_display = ('nombre_original', 'tipo', 'consulta', 'subido_en')
    list_filter = ('tipo',)
    readonly_fields = ('subido_en',)
