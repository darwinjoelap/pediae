from django.http import request
from django.shortcuts import render, get_object_or_404, redirect
import consultas
from pediae.decorators import tenant_login_required as login_required
from django.contrib import messages
from servicios.models import Servicio
from datetime import date
from consultas.models import Procedimiento
from django.db.models import Q
from .models import Paciente
from .forms import PacienteAsistenteForm, PacientePersonalForm, PacienteCompletoForm, PacienteDoctoraNuevoForm


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


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

    # Buscar última cita sin consulta registrada (atendida o programada)
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

    # Datos de evolución para gráficas (solo si es médico)
    graficas_json = None
    if request.user.es_medico and consultas is not None:
        import json
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
            f = p['fecha'].strftime('%d/%m/%Y')
            fechas.append(f)
            pesos.append(float(p['peso']) if p['peso'] else None)
            tallas.append(float(p['talla']) if p['talla'] else None)
            pcs.append(float(p['perimetro_cefalico']) if p['perimetro_cefalico'] else None)
            p_peso.append(p['percentil_peso'])
            p_talla.append(p['percentil_talla'])
            p_pc.append(p['percentil_pc'])
        graficas_json = json.dumps({
            'fechas': fechas,
            'pesos': pesos,
            'tallas': tallas,
            'pcs': pcs,
            'p_peso': p_peso,
            'p_talla': p_talla,
            'p_pc': p_pc,
        })

    return render(request, 'pacientes/detalle.html', {
        'paciente': paciente,
        'consultas': consultas,
        'citas': citas,
        'ultima_cita_sin_consulta': ultima_cita_sin_consulta,
        'servicios_disponibles': servicios_disponibles,
        'procedimientos': procedimientos,
        'graficas_json': graficas_json,
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