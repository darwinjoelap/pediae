from django.shortcuts import redirect


def tenant_login_required(view_func):
    """Login required que redirige al login del tenant, no al de settings."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            tenant = getattr(request, 'tenant', None)
            if tenant:
                return redirect(f'/t/{tenant.slug}/accounts/login/?next={request.path}')
            return redirect(f'/panel/login/')
        return view_func(request, *args, **kwargs)
    return wrapper
