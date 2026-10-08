from django.contrib import admin
from .models import SolicitudIdempotente


@admin.register(SolicitudIdempotente)
class SolicitudIdempotenteAdmin(admin.ModelAdmin):
    list_display = ('ruta', 'estado', 'usuario_id', 'creado')
    list_filter = ('estado',)
    search_fields = ('ruta', 'clave')
