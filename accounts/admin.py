from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'rol', 'sexo', 'tenant', 'is_active')
    list_filter = ('rol', 'sexo', 'is_active', 'tenant')
    fieldsets = UserAdmin.fieldsets + (
        ('Datos del consultorio', {'fields': ('rol', 'sexo', 'tenant')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos del consultorio', {'fields': ('rol', 'sexo', 'tenant')}),
    )