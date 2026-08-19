from django.contrib import admin
from .models import ConfigConsultorio


@admin.register(ConfigConsultorio)
class ConfigConsultorioAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'nombre_medico', 'especialidad', 'actualizado_en']