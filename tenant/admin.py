from django.contrib import admin
from .models import Plan, Tenant, Suscripcion


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'precio', 'max_pacientes', 'max_usuarios', 'activo']
    list_editable = ['activo']


class SuscripcionInline(admin.TabularInline):
    model = Suscripcion
    extra = 1
    fields = ['plan', 'estado', 'fecha_inicio', 'fecha_fin', 'renovacion_automatica']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'email', 'activo', 'creado_en']
    list_editable = ['activo']
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [SuscripcionInline]


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'estado', 'fecha_inicio', 'fecha_fin', 'dias_restantes']
    list_filter = ['estado', 'plan']
    search_fields = ['tenant__nombre']