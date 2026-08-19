from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect, FileResponse
from django.conf import settings
import os


def root_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return HttpResponseRedirect('/panel/')
        tenant = getattr(request, 'tenant', None)
        if tenant:
            return HttpResponseRedirect(f'/t/{tenant.slug}/agenda/')
    return HttpResponseRedirect('/panel/login/')


def sw_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


urlpatterns = [
    path('sw.js', sw_view),
    path('admin/', admin.site.urls),
    path('panel/', include('panel.urls')),
    path('t/<slug:tenant_slug>/', include('ginea.tenant_urls')),
    path('', root_redirect),
]