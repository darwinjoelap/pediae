from django.shortcuts import render, get_object_or_404, redirect
from pediae.decorators import tenant_login_required as login_required
from django.contrib import messages
from django.db.models import Q
from django.db import models as _m
from datetime import date

from .models import Paciente, Vacuna, VacunaAplicada
from .forms import PacienteAsistenteForm, PacientePersonalForm, PacienteCompletoForm, PacienteDoctoraNuevoForm


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


# ── Pacientes ──────────────────────────────────────────────────────────────────

@login_required
def lista_pacientes(request):
    tenant = request.tenant
    q = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.filter(tenant=tenant)
    if q:
        pacientes = pacientes.filter(
            Q(nombre_completo__icontains=q) | Q(cedula__icontains=q) | Q(telefono__icontains=q)
        )
    return render(request, 'pacientes/lista.html', {'pacientes': pacientes, 'q': q})


@login_required
def nueva_paciente(request):
    if request.user.es_medico:
        FormClass = PacienteDoctoraNuevoForm
    else:
        FormClass = PacienteAsistenteForm

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            paciente.tenant = request.tenant
            paciente.save()
            messages.success(request, f'Paciente {paciente.nombre_completo} registrada.')
            if request.user.es_medico:
                accion = request.POST.get('accion', 'solo_guardar')
                if accion == 'historia':
                    return _r(request, f'/pacientes/{paciente.pk}/editar/')
                elif accion == 'cita':
                    return _r(request, f'/agenda/citas/nueva/?paciente={paciente.pk}')
            return _r(request, f'/pacientes/{paciente.pk}/')
    else:
        form = FormClass()

    return render(request, 'pacientes/form.html', {
        'form': form,
        'titulo': 'Registrar paciente',
        'modo_nuevo_doctora': request.user.es_medico,
    })


@login_required
def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    consultas = paciente.consultas.all().prefetch_related('adjuntos') if request.user.es_medico else None
    citas = paciente.citas.filter(tenant=request.tenant).order_by('-fecha', '-hora_inicio')[:10]

    from agenda.models import Cita
    from servicios.models import Servicio
    from consultas.models import Procedimiento

    ultima_cita_sin_consulta = Cita.objects.filter(
        paciente=paciente,
        tenant=request.tenant,
        consulta__isnull=True,
        fecha__gte=date.today(),
    ).order_by('fecha', 'hora_inicio').first()

    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )

    procedimientos = Procedimiento.objects.filter(
        paciente=paciente, tenant=request.tenant
    ).select_related('servicio')

    # Vacunas: resumen para el perfil (atrasadas + próximas pendientes)
    vacunas_resumen = _vacunas_resumen(paciente, request.tenant)

    # Datos de evolución para gráficas (solo si es médico)
    graficas_json = None
    if request.user.es_medico and consultas is not None:
        from django.core.serializers.json import DjangoJSONEncoder
        import json

        def _f(v, decimals=1):
            return round(float(v), decimals) if v is not None else None

        puntos = (
            paciente.consultas
            .filter(tenant=request.tenant)
            .exclude(peso__isnull=True, talla__isnull=True, perimetro_cefalico__isnull=True)
            .order_by('fecha')
            .values('fecha', 'peso', 'talla', 'perimetro_cefalico',
                    'percentil_peso', 'percentil_talla', 'percentil_pc')
        )
        fechas, pesos, tallas, pcs = [], [], [], []
        p_peso, p_talla, p_pc = [], [], []
        for p in puntos:
            fechas.append(p['fecha'].strftime('%d/%m/%Y'))
            pesos.append(_f(p['peso'], 2))
            tallas.append(_f(p['talla'], 1))
            pcs.append(_f(p['perimetro_cefalico'], 1))
            p_peso.append(_f(p['percentil_peso'], 0))
            p_talla.append(_f(p['percentil_talla'], 0))
            p_pc.append(_f(p['percentil_pc'], 0))
        graficas_json = json.dumps({
            'fechas': fechas,
            'pesos': pesos,
            'tallas': tallas,
            'pcs': pcs,
            'p_peso': p_peso,
            'p_talla': p_talla,
            'p_pc': p_pc,
        }, cls=DjangoJSONEncoder)

    return render(request, 'pacientes/detalle.html', {
        'paciente': paciente,
        'consultas': consultas,
        'citas': citas,
        'ultima_cita_sin_consulta': ultima_cita_sin_consulta,
        'servicios_disponibles': servicios_disponibles,
        'procedimientos': procedimientos,
        'graficas_json': graficas_json,
        'vacunas_resumen': vacunas_resumen,
    })


@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    FormClass = PacienteCompletoForm if request.user.es_medico else PacientePersonalForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=paciente)
        if form.is_valid():
            p = form.save(commit=False)
            p.tenant = request.tenant
            p.save()
            messages.success(request, 'Ficha actualizada correctamente.')
            return _r(request, f'/pacientes/{paciente.pk}/')
    else:
        form = FormClass(instance=paciente)

    return render(request, 'pacientes/form.html', {
        'form': form,
        'paciente': paciente,
        'titulo': 'Editar ficha',
    })


# ── Vacunas ────────────────────────────────────────────────────────────────────

def _vacunas_resumen(paciente, tenant):
    """Para el perfil: dict con conteos y listas cortas."""
    edad_meses = paciente.get_edad_en_meses()

    vacunas = Vacuna.objects.filter(activa=True).filter(
        _m.Q(tenant=None) | _m.Q(tenant=tenant)
    ).order_by('orden', 'edad_recomendada_meses', 'dosis_numero')

    aplicadas_ids = set(
        VacunaAplicada.objects.filter(paciente=paciente, tenant=tenant)
        .values_list('vacuna_id', flat=True)
    )

    total = vacunas.count()
    aplicadas = len(aplicadas_ids)
    atrasadas = []
    proximas = []

    for v in vacunas:
        if v.pk in aplicadas_ids:
            continue
        if edad_meses is None:
            continue
        if v.edad_max_meses and edad_meses > v.edad_max_meses:
            atrasadas.append(v)
        elif v.edad_recomendada_meses <= edad_meses:
            proximas.append(v)

    return {
        'total': total,
        'aplicadas': aplicadas,
        'pendientes': total - aplicadas,
        'atrasadas': atrasadas,
        'proximas': proximas[:3],  # máximo 3 en resumen
    }


def _estado_esquema(paciente, tenant):
    """Esquema completo con estado por dosis."""
    edad_meses = paciente.get_edad_en_meses()

    vacunas = Vacuna.objects.filter(activa=True).filter(
        _m.Q(tenant=None) | _m.Q(tenant=tenant)
    ).order_by('orden', 'edad_recomendada_meses', 'dosis_numero')

    aplicadas_map = {
        va.vacuna_id: va
        for va in VacunaAplicada.objects.filter(
            paciente=paciente, tenant=tenant
        ).select_related('vacuna')
    }

    resultado = []
    for v in vacunas:
        aplicada = aplicadas_map.get(v.pk)
        if aplicada:
            estado = 'aplicada'
        elif edad_meses is None:
            estado = 'pendiente'
        elif v.edad_max_meses and edad_meses > v.edad_max_meses:
            estado = 'atrasada'
        elif edad_meses >= v.edad_recomendada_meses:
            estado = 'pendiente'
        else:
            estado = 'futura'
        resultado.append({'vacuna': v, 'estado': estado, 'aplicada': aplicada})

    return resultado


@login_required
def vacunas_paciente(request, pk):
    """Página completa del esquema de vacunación."""
    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    esquema = _estado_esquema(paciente, request.tenant)

    return render(request, 'pacientes/vacunas.html', {
        'paciente': paciente,
        'esquema': esquema,
        'aplicadas': [e for e in esquema if e['estado'] == 'aplicada'],
        'pendientes': [e for e in esquema if e['estado'] == 'pendiente'],
        'atrasadas': [e for e in esquema if e['estado'] == 'atrasada'],
        'futuras': [e for e in esquema if e['estado'] == 'futura'],
        'today': date.today(),
    })


@login_required
def registrar_vacuna(request, pk):
    """POST: registrar dosis aplicada."""
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para registrar vacunas.')
        return _r(request, f'/pacientes/{pk}/vacunas/')

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        vacuna_id = request.POST.get('vacuna_id')
        fecha = request.POST.get('fecha')
        lote = request.POST.get('lote', '').strip()
        obs = request.POST.get('observaciones', '').strip()

        if not vacuna_id or not fecha:
            messages.error(request, 'Selecciona la vacuna y la fecha.')
            return _r(request, f'/pacientes/{pk}/vacunas/')

        try:
            vacuna = Vacuna.objects.get(pk=vacuna_id, activa=True)
        except Vacuna.DoesNotExist:
            messages.error(request, 'Vacuna no encontrada.')
            return _r(request, f'/pacientes/{pk}/vacunas/')

        obj, created = VacunaAplicada.objects.get_or_create(
            paciente=paciente,
            vacuna=vacuna,
            defaults=dict(
                tenant=request.tenant,
                fecha=fecha,
                lote=lote,
                observaciones=obs,
                aplicada_por=request.user,
            ),
        )
        if not created:
            obj.fecha = fecha
            obj.lote = lote
            obj.observaciones = obs
            obj.aplicada_por = request.user
            obj.save()

        messages.success(request, f'✓ {vacuna.nombre} (d{vacuna.dosis_numero}) registrada.')

    return _r(request, f'/pacientes/{pk}/vacunas/')


@login_required
def eliminar_vacuna_aplicada(request, pk, va_pk):
    """POST: eliminar registro de vacuna aplicada."""
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, f'/pacientes/{pk}/vacunas/')

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    va = get_object_or_404(VacunaAplicada, pk=va_pk, paciente=paciente, tenant=request.tenant)

    if request.method == 'POST':
        nombre = f'{va.vacuna.nombre} d{va.vacuna.dosis_numero}'
        va.delete()
        messages.success(request, f'Registro de {nombre} eliminado.')

    return _r(request, f'/pacientes/{pk}/vacunas/')
