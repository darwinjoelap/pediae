from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache


@never_cache
def ping(request):
    """Respuesta mínima para medir la conexión desde offline.js."""
    user = getattr(request, 'user', None)
    return JsonResponse({'ok': True, 'auth': bool(user and user.is_authenticated)})


@never_cache
def precache(request):
    """
    Lista de páginas que offline.js descarga por adelantado (con buena señal) para
    poder trabajar sin datos: agenda de hoy y mañana, lista de pacientes, ficha de
    cada paciente citado y su formulario de "Nueva consulta".
    """
    user = request.user
    if not user.is_authenticated or not getattr(user, 'tenant_id', None):
        return JsonResponse({'urls': []})

    from agenda.models import Cita

    tenant = user.tenant
    prefix = '' if getattr(settings, 'TENANT_SLUG', '') else f'/t/{tenant.slug}'
    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)

    urls = [f'{prefix}/agenda/', f'{prefix}/agenda/{manana.isoformat()}/', f'{prefix}/pacientes/']
    citas = (
        Cita.objects.filter(tenant=tenant, fecha__gte=hoy, fecha__lte=manana)
        .exclude(estado__in=['cancelada', 'no_asistio'])
        .order_by('fecha', 'hora_inicio')[:40]
    )
    es_medico = getattr(user, 'es_medico', False)
    vistos = set()
    for cita in citas:
        if cita.paciente_id not in vistos:
            vistos.add(cita.paciente_id)
            urls.append(f'{prefix}/pacientes/{cita.paciente_id}/')
        if es_medico and cita.estado != 'atendida':
            urls.append(f'{prefix}/consultas/nueva/{cita.paciente_id}/?cita={cita.pk}')

    return JsonResponse({'urls': urls[:80]})
