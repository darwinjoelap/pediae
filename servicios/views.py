from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ginea.decorators import tenant_login_required as login_required
from .models import Servicio, TasaCambio
from .forms import ServicioForm, TasaCambioForm


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


@login_required
def lista_servicios(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    tenant = request.tenant
    servicios = Servicio.objects.filter(tenant=tenant)
    try:
        tasa = tenant.tasa_cambio
    except TasaCambio.DoesNotExist:
        tasa = None
    tasa_form = TasaCambioForm(instance=tasa)
    return render(request, 'servicios/lista.html', {
        'servicios': servicios,
        'tasa': tasa,
        'tasa_form': tasa_form,
    })


@login_required
def guardar_tasa(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    if request.method == 'POST':
        tenant = request.tenant
        try:
            tasa = tenant.tasa_cambio
        except TasaCambio.DoesNotExist:
            tasa = TasaCambio(tenant=tenant)
        form = TasaCambioForm(request.POST, instance=tasa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tasa de cambio actualizada.')
    return _r(request, '/servicios/')


@login_required
def crear_servicio(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.tenant = request.tenant
            s.save()
            messages.success(request, f'Servicio "{s.nombre}" creado.')
            return _r(request, '/servicios/')
    else:
        form = ServicioForm()
    return render(request, 'servicios/form.html', {'form': form, 'titulo': 'Nuevo servicio'})


@login_required
def editar_servicio(request, pk):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    servicio = get_object_or_404(Servicio, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio actualizado.')
            return _r(request, '/servicios/')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'servicios/form.html', {
        'form': form, 'titulo': f'Editar {servicio.nombre}', 'servicio': servicio
    })


@login_required
def toggle_servicio(request, pk):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    servicio = get_object_or_404(Servicio, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        servicio.activo = not servicio.activo
        servicio.save(update_fields=['activo'])
        estado = 'activado' if servicio.activo else 'desactivado'
        messages.success(request, f'"{servicio.nombre}" {estado}.')
    return _r(request, '/servicios/')