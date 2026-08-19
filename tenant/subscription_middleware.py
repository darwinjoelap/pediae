from django.shortcuts import render, redirect


RUTAS_LIBRES = [
    '/admin/',
    '/panel/',
    '/static/',
]


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)
        # Manifest siempre libre para PWA
        if request.path.endswith('/manifest.json'):
            return self.get_response(request)

        for ruta in RUTAS_LIBRES:
            if request.path.startswith(ruta):
                return self.get_response(request)

        tenant = getattr(request, 'tenant', None)

        if not request.user.is_authenticated:
            if tenant and not request.path.endswith('/login/'):
                return redirect(f'/t/{tenant.slug}/accounts/login/?next={request.path}')
            return self.get_response(request)

        if not tenant:
            return self.get_response(request)

        if not tenant.activo:
            return render(request, 'tenant/suspendido.html', status=403)

        if not tenant.suscripcion_activa:
            return render(request, 'tenant/vencida.html', status=403)

        # Alerta de vencimiento próximo (5 días o menos)
        sus = tenant.suscripcion_activa
        if sus and sus.dias_restantes <= 5:
            request.suscripcion_dias_restantes = sus.dias_restantes
        else:
            request.suscripcion_dias_restantes = None

        # Superusuarios pueden acceder a cualquier tenant
        if request.user.is_superuser:
            return self.get_response(request)

        # Verificar que el usuario pertenece a este tenant
        if request.user.tenant_id != tenant.id:
            return render(request, 'tenant/acceso_denegado.html', status=403)

        return self.get_response(request)