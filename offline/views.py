from django.http import JsonResponse
from django.views.decorators.cache import never_cache


@never_cache
def ping(request):
    """Respuesta mínima para medir la conexión desde offline.js."""
    user = getattr(request, 'user', None)
    return JsonResponse({'ok': True, 'auth': bool(user and user.is_authenticated)})
