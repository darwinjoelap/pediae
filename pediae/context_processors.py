from configuracion.models import ConfigConsultorio


def consultorio_info(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return {
            'CONSULTORIO_NOMBRE': 'Pediae',
            'CONSULTORIO_ESPECIALIDAD': '',
            'TENANT_PREFIX': '',
            'COLOR_PRIMARIO': '#2AACA8',
        }
    try:
        config = tenant.config
        color = config.color_primario or '#2AACA8'
        return {
            'CONSULTORIO_NOMBRE': config.nombre_display(),
            'CONSULTORIO_ESPECIALIDAD': config.especialidad,
            'CONSULTORIO_CONFIG': config,
            'TENANT_PREFIX': f'/t/{tenant.slug}',
            'COLOR_PRIMARIO': color,
        }
    except ConfigConsultorio.DoesNotExist:
        return {
            'CONSULTORIO_NOMBRE': tenant.nombre,
            'CONSULTORIO_ESPECIALIDAD': '',
            'CONSULTORIO_CONFIG': None,
            'TENANT_PREFIX': f'/t/{tenant.slug}',
            'COLOR_PRIMARIO': '#2AACA8',
        }
