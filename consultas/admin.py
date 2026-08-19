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
            return format_html('<a href="{}" target="_blank">Ver en Drive</a>', obj.get_url())
        return '—'
    get_url_display.short_description = 'Enlace'


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha', 'motivo_consulta', 'diagnostico', 'es_prenatal', 'creado_en')
    list_filter = ('es_prenatal', 'fecha')
    search_fields = ('paciente__nombre_completo', 'paciente__cedula', 'diagnostico')
    date_hierarchy = 'fecha'
    readonly_fields = ('creado_en',)
    inlines = [AdjuntoInline]
    fieldsets = (
        ('Datos básicos', {
            'fields': ('paciente', 'cita', 'fecha', 'peso', 'tension_arterial')
        }),
        ('Clínica', {
            'fields': ('motivo_consulta', 'sintomas_actuales', 'examen_fisico',
                       'diagnostico', 'tratamiento', 'proxima_cita', 'observaciones')
        }),
        ('Control prenatal', {
            'fields': ('es_prenatal', 'fpp', 'semanas_gestacion',
                       'altura_uterina', 'fcf', 'presentacion_fetal', 'edemas'),
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
