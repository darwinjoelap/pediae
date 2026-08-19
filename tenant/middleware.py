from .models import Tenant


class TenantMiddleware:
    """
    Resuelve el tenant activo a partir del path de la request.
    /t/<slug>/... → tenant con ese slug
    TENANT_SLUG en settings → instancia dedicada (modo legacy)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = self._resolver(request)
        return self.get_response(request)

    def _resolver(self, request):
        from django.conf import settings

        # Modo 1: variable de entorno (instancia dedicada Railway)
        slug = getattr(settings, 'TENANT_SLUG', None)
        if slug:
            try:
                return Tenant.objects.get(slug=slug, activo=True)
            except Tenant.DoesNotExist:
                return None

        # Modo 2: path /t/<slug>/
        partes = request.path.strip('/').split('/')
        if len(partes) >= 2 and partes[0] == 't':
            slug = partes[1]
            try:
                return Tenant.objects.get(slug=slug, activo=True)
            except Tenant.DoesNotExist:
                return None

        return None


class StripTenantSlugMiddleware:
    """Elimina tenant_slug de los kwargs para que no llegue a las vistas."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        view_kwargs.pop('tenant_slug', None)
        return None