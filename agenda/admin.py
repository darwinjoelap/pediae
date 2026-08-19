from django.contrib import admin
from .models import LugarConsulta, Cita


@admin.register(LugarConsulta)
class LugarConsultaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'activo', 'orden')
    list_editable = ('activo', 'orden')
    search_fields = ('nombre',)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha', 'hora_inicio', 'lugar', 'motivo', 'estado', 'recordatorio_enviado')
    list_filter = ('estado', 'fecha', 'lugar', 'recordatorio_enviado')
    search_fields = ('paciente__nombre_completo', 'paciente__cedula', 'motivo')
    date_hierarchy = 'fecha'
    readonly_fields = ('creado_en', 'creado_por', 'recordatorio_fecha')
    fieldsets = (
        ('Datos de la cita', {
            'fields': ('paciente', 'fecha', 'hora_inicio', 'hora_fin', 'lugar', 'motivo', 'estado', 'notas')
        }),
        ('Recordatorio', {
            'fields': ('recordatorio_enviado', 'recordatorio_fecha', 'recordatorio_canal'),
            'classes': ('collapse',),
        }),
        ('Control', {
            'fields': ('creado_por', 'creado_en'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
