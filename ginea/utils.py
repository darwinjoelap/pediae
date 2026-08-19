def tenant_redirect(request, viewname):
    """
    Construye una URL con el prefijo del tenant activo.
    Uso: return tenant_redirect(request, 'agenda:hoy')
    """
    from django.http import HttpResponseRedirect
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    
    # Mapeo de nombres de vista a paths
    rutas = {
        'agenda:hoy': '/agenda/',
        'agenda:semana': '/agenda/semana/',
        'agenda:lugares': '/agenda/lugares/',
        'pacientes:lista': '/pacientes/',
        'pacientes:nuevo': '/pacientes/nuevo/',
        'consultas:lista': '/consultas/',
        'configuracion:editar': '/configuracion/',
    }
    
    path = rutas.get(viewname, '/')
    return HttpResponseRedirect(f'{prefix}{path}')