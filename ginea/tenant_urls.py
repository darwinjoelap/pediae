from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse
import json as json_module
from django.http import HttpResponse


def manifest_view(request, **kwargs):
    tenant = getattr(request, 'tenant', None)
    slug = tenant.slug if tenant else 'app'
    prefix = f'/t/{slug}'

    try:
        nombre = tenant.config.nombre_medico or tenant.nombre if tenant else 'Ginea'
        especialidad = tenant.config.especialidad if tenant else ''
    except Exception:
        nombre = tenant.nombre if tenant else 'Ginea'
        especialidad = ''

    manifest = {
        "name": f"Ginea - {nombre}",
        "short_name": "Ginea",
        "description": especialidad or "Sistema de gestión de consultorio",
        "start_url": f"{prefix}/agenda/",
        "scope": f"{prefix}/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#2AACA8",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/static/icons/icon-72x72.png",   "sizes": "72x72",   "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-96x96.png",   "sizes": "96x96",   "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-128x128.png", "sizes": "128x128", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-144x144.png", "sizes": "144x144", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-152x152.png", "sizes": "152x152", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "/static/icons/icon-384x384.png", "sizes": "384x384", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ]
    }
    json_str = json_module.dumps(manifest, ensure_ascii=False)
    return HttpResponse(json_str, content_type='application/manifest+json; charset=utf-8')


urlpatterns = [
    path('', RedirectView.as_view(url='agenda/', permanent=False)),
    path('manifest.json', manifest_view, name='manifest'),
    path('accounts/', include('accounts.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('agenda/', include('agenda.urls')),
    path('consultas/', include('consultas.urls')),
    path('configuracion/', include('configuracion.urls')),
    path('reportes/', include('reportes.urls')),
    path('servicios/', include('servicios.urls')),
]