"""
IdempotenciaMiddleware — evita duplicados cuando un formulario se envía más de una vez.

Va AL FINAL de MIDDLEWARE (después de MessageMiddleware) para tener request.user,
request.tenant y mensajes disponibles.

Solo actúa en POST que traen `_idem_key` (lo agrega offline.js). Todo lo demás pasa igual.
"""
import random
import re
from datetime import timedelta

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone

from .models import SolicitudIdempotente

CLAVE_RE = re.compile(r'^[A-Za-z0-9-]{8,64}$')
HEADER_OFFLINE = 'HTTP_X_OFFLINE_FORM'      # lo envía offline.js cuando usa fetch
MINUTOS_PROCESANDO = 2                       # pasado esto, un "procesando" se considera huérfano
DIAS_RETENCION = 7


def _clave(request):
    clave = (request.META.get('HTTP_X_IDEMPOTENCY_KEY') or '').strip()
    if not clave:
        try:
            clave = (request.POST.get('_idem_key') or '').strip()
        except Exception:
            clave = ''
    return clave if CLAVE_RE.match(clave) else ''


def _como_json_si_fetch(request, location):
    """Con fetch, una redirección se devuelve como JSON para que el JS navegue él mismo."""
    if request.META.get(HEADER_OFFLINE):
        return JsonResponse({'ok': True, 'redirect': location})
    return HttpResponseRedirect(location)


class IdempotenciaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != 'POST':
            return self.get_response(request)
        clave = _clave(request)
        if not clave:
            return self.get_response(request)

        user = getattr(request, 'user', None)
        usuario_id = user.pk if user is not None and user.is_authenticated else None
        clave_db = f'{usuario_id or 0}:{clave}'

        # Limpieza ocasional de registros viejos (≈1 de cada 50 POST)
        if random.random() < 0.02:
            SolicitudIdempotente.objects.filter(
                creado__lt=timezone.now() - timedelta(days=DIAS_RETENCION)).delete()

        try:
            with transaction.atomic():
                registro = SolicitudIdempotente.objects.create(
                    clave=clave_db, usuario_id=usuario_id, ruta=request.path[:300])
        except IntegrityError:
            previo = SolicitudIdempotente.objects.filter(clave=clave_db).first()
            if previo is None:
                return self.get_response(request)
            if previo.estado == SolicitudIdempotente.OK:
                messages.info(request, 'Esta información ya se había guardado. No se duplicó.')
                return _como_json_si_fetch(request, previo.location or request.path)
            if previo.creado > timezone.now() - timedelta(minutes=MINUTOS_PROCESANDO):
                # La primera petición sigue en curso (red lenta): que el navegador reintente luego
                return JsonResponse({'ok': False, 'estado': 'procesando'}, status=409)
            # Huérfano (el servidor se cayó a mitad): se toma el relevo
            previo.creado = timezone.now()
            previo.save(update_fields=['creado'])
            registro = previo

        response = self.get_response(request)

        location = response.get('Location', '') if response.status_code in (301, 302, 303) else ''
        if location and '/login' in location:
            # Sesión vencida: no se guardó nada → liberar la clave y avisar al JS
            registro.delete()
            if request.META.get(HEADER_OFFLINE):
                return JsonResponse({'ok': False, 'login': True, 'redirect': location}, status=401)
            return response

        if location:
            registro.estado = SolicitudIdempotente.OK
            registro.location = response['Location'][:500]
            registro.save(update_fields=['estado', 'location'])
            if request.META.get(HEADER_OFFLINE):
                nueva = JsonResponse({'ok': True, 'redirect': response['Location']})
                nueva.cookies = response.cookies   # conserva mensajes / sesión
                return nueva
            return response

        # 200 con errores de formulario, 4xx o 5xx: se libera la clave para poder reintentar
        registro.delete()
        return response
