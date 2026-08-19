from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

import tenant
from .models import Cita, LugarConsulta
from pacientes.models import Paciente
from consultas.models import Consulta, Procedimiento
from ginea.decorators import tenant_login_required as login_required
import json
from django.http import JsonResponse
from django.utils import timezone


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


@login_required
def agenda_hoy(request):
    return agenda_dia(request, fecha=date.today().isoformat())

@login_required
def agenda_dia(request, fecha):
    try:
        fecha_obj = date.fromisoformat(fecha)
    except ValueError:
        fecha_obj = date.today()

    tenant = request.tenant
    citas = Cita.objects.filter(
        fecha=fecha_obj, tenant=tenant
    ).select_related('paciente', 'lugar', 'creado_por')

    dia_anterior = (fecha_obj - timedelta(days=1)).isoformat()
    dia_siguiente = (fecha_obj + timedelta(days=1)).isoformat()

    resumen = {
        'total': citas.count(),
        'atendidas': citas.filter(estado='atendida').count(),
        'pendientes': citas.filter(estado__in=['programada', 'confirmada']).count(),
        'canceladas': citas.filter(estado__in=['cancelada', 'no_asistio']).count(),
    }

    from consultas.models import Consulta, Procedimiento
    from servicios.models import Servicio

    for cita in citas:
        cita.whatsapp_url = cita.get_whatsapp_url(tenant=tenant)
        cita.consulta_registrada = None
        cita.procedimiento_registrado = None

        if cita.estado == 'atendida':
            try:
                cita.consulta_registrada = cita.consulta
            except Exception:
                # Buscar consulta vinculada a esta cita específica
                cita.consulta_registrada = Consulta.objects.filter(
                    cita=cita,
                ).first()

            if not cita.consulta_registrada:
                # Buscar procedimiento vinculado a esta cita específica
                cita.procedimiento_registrado = Procedimiento.objects.filter(
                    cita=cita,
                ).first()

    consultas_sin_cita = Consulta.objects.filter(
        tenant=tenant, fecha=fecha_obj, cita__isnull=True,
    ).select_related('paciente', 'lugar', 'medico').prefetch_related('servicios_usados')

    procedimientos_sin_cita = Procedimiento.objects.filter(
        tenant=tenant, fecha=fecha_obj, cita__isnull=True,
    ).select_related('paciente', 'servicio', 'medico')

    servicios_disponibles = Servicio.objects.filter(tenant=tenant, activo=True)

    return render(request, 'agenda/dia.html', {
        'fecha': fecha_obj,
        'citas': citas,
        'dia_anterior': dia_anterior,
        'dia_siguiente': dia_siguiente,
        'es_hoy': fecha_obj == date.today(),
        'resumen': resumen,
        'tenant': tenant,
        'consultas_sin_cita': consultas_sin_cita,
        'procedimientos_sin_cita': procedimientos_sin_cita,
        'servicios_disponibles': servicios_disponibles,
    })

@login_required
def agenda_semana(request):
    hoy = date.today()
    tenant = request.tenant
    inicio_str = request.GET.get('inicio')
    if inicio_str:
        try:
            inicio_semana = date.fromisoformat(inicio_str)
        except ValueError:
            inicio_semana = hoy - timedelta(days=hoy.weekday())
    else:
        inicio_semana = hoy - timedelta(days=hoy.weekday())

    dias = []
    for i in range(6):
        dia = inicio_semana + timedelta(days=i)
        citas = Cita.objects.filter(
            fecha=dia, tenant=tenant
        ).select_related('paciente', 'lugar')
        dias.append({'fecha': dia, 'citas': citas})

    return render(request, 'agenda/semana.html', {
        'dias': dias,
        'semana_anterior': (inicio_semana - timedelta(days=7)).isoformat(),
        'semana_siguiente': (inicio_semana + timedelta(days=7)).isoformat(),
    })


@login_required
def nueva_cita(request):
    from .forms import CitaForm
    from servicios.models import Servicio
    paciente_id = request.GET.get('paciente')
    fecha_inicial = request.GET.get('fecha', date.today().isoformat())
    initial = {'fecha': fecha_inicial}
    paciente = None
    if paciente_id:
        paciente = get_object_or_404(Paciente, pk=paciente_id, tenant=request.tenant)
        initial['paciente'] = paciente

    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )

    if request.method == 'POST':
        form = CitaForm(request.POST, user=request.user, request=request)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.creado_por = request.user
            cita.tenant = request.tenant
            cita.save()
            form.save_m2m()
            servicios_ids = request.POST.getlist('servicios_manual')
            if servicios_ids:
                for sid in servicios_ids:
                    try:
                        srv = Servicio.objects.get(pk=sid, tenant=request.tenant, activo=True)
                        cita.servicios.add(srv)
                    except Servicio.DoesNotExist:
                        pass
            messages.success(request, f'Cita agendada para {cita.paciente.nombre_completo}.')
            return _r(request, f'/agenda/{cita.fecha.isoformat()}/')
    else:
        form = CitaForm(initial=initial, user=request.user, request=request)

    return render(request, 'agenda/cita_form.html', {
        'form': form,
        'paciente': paciente,
        'titulo': 'Nueva cita',
        'servicios_disponibles': servicios_disponibles,
    })


@login_required
def editar_cita(request, pk):
    from .forms import CitaForm
    cita = get_object_or_404(Cita, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita, user=request.user, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cita actualizada.')
            return _r(request, f'/agenda/{cita.fecha.isoformat()}/')
    else:
        form = CitaForm(instance=cita, user=request.user, request=request)

    return render(request, 'agenda/cita_form.html', {
        'form': form, 'cita': cita, 'titulo': 'Editar cita',
    })


@login_required
def marcar_atendida(request, pk):
    cita = get_object_or_404(Cita, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        cita.estado = 'atendida'
        cita.save(update_fields=['estado'])
        messages.success(request, f'Cita de {cita.paciente.nombre_completo} marcada como atendida.')
    return _r(request, f'/agenda/{cita.fecha.isoformat()}/')

@login_required
def marcar_recordatorio(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    cita = get_object_or_404(Cita, pk=pk, tenant=request.tenant)
    try:
        data = json.loads(request.body)
        canal = data.get('canal', 'whatsapp')
    except Exception:
        canal = 'whatsapp'
    cita.recordatorio_enviado = True
    cita.recordatorio_fecha = timezone.now()
    cita.recordatorio_canal = canal
    cita.save(update_fields=['recordatorio_enviado', 'recordatorio_fecha', 'recordatorio_canal'])
    return JsonResponse({'ok': True})


@login_required
def lista_lugares(request):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para gestionar lugares.')
        return _r(request, '/agenda/')
    lugares = LugarConsulta.objects.filter(tenant=request.tenant)
    return render(request, 'agenda/lugares.html', {'lugares': lugares})


@login_required
def nuevo_lugar(request):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, '/agenda/')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if nombre:
            LugarConsulta.objects.create(
                tenant=request.tenant,
                nombre=nombre,
                direccion=request.POST.get('direccion', '').strip(),
                telefono=request.POST.get('telefono', '').strip(),
                orden=int(request.POST.get('orden', 0)),
            )
            messages.success(request, f'Lugar "{nombre}" agregado.')
        else:
            messages.error(request, 'El nombre es obligatorio.')
    return _r(request, '/agenda/lugares/')


@login_required
def editar_lugar(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, '/agenda/')
    lugar = get_object_or_404(LugarConsulta, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if nombre:
            lugar.nombre = nombre
            lugar.direccion = request.POST.get('direccion', '').strip()
            lugar.telefono = request.POST.get('telefono', '').strip()
            lugar.orden = int(request.POST.get('orden', 0))
            lugar.save()
            messages.success(request, f'Lugar "{nombre}" actualizado.')
        else:
            messages.error(request, 'El nombre es obligatorio.')
    return _r(request, '/agenda/lugares/')


@login_required
def toggle_lugar(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, '/agenda/')
    lugar = get_object_or_404(LugarConsulta, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        lugar.activo = not lugar.activo
        lugar.save(update_fields=['activo'])
        estado = 'activado' if lugar.activo else 'desactivado'
        messages.success(request, f'Lugar "{lugar.nombre}" {estado}.')
    return _r(request, '/agenda/lugares/')


@login_required
def eliminar_lugar(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, '/agenda/')
    lugar = get_object_or_404(LugarConsulta, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        nombre = lugar.nombre
        lugar.delete()
        messages.success(request, f'Lugar "{nombre}" eliminado.')
    return _r(request, '/agenda/lugares/')

@login_required
def eliminar_cita(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, '/agenda/')
    cita = get_object_or_404(Cita, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        if cita.estado == 'atendida':
            messages.error(request, 'No se puede eliminar una cita atendida.')
            return _r(request, f'/agenda/{cita.fecha.isoformat()}/')
        fecha = cita.fecha.isoformat()
        cita.delete()
        messages.success(request, 'Cita eliminada.')
        return _r(request, f'/agenda/{fecha}/')
    return _r(request, f'/agenda/{cita.fecha.isoformat()}/')
