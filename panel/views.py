from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from tenant.models import Tenant, Suscripcion, Plan


def panel_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/panel/login/?next={request.path}')
        if not request.user.is_superuser:
            return redirect('/panel/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def panel_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/panel/')

    error = False
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect(request.GET.get('next', '/panel/'))
        error = True

    return render(request, 'panel/login.html', {'error': error})


def panel_logout(request):
    if request.method == 'POST':
        logout(request)
    return redirect('/panel/login/')


@panel_required
def dashboard(request):
    tenants = Tenant.objects.prefetch_related('suscripciones__plan').all()

    hoy = timezone.now().date()
    proximos_vencer = Suscripcion.objects.filter(
        estado='activa',
        fecha_fin__lte=hoy + timedelta(days=30),
        fecha_fin__gte=hoy,
    ).select_related('tenant', 'plan').order_by('fecha_fin')

    stats = {
        'total': tenants.count(),
        'activos': tenants.filter(activo=True).count(),
        'inactivos': tenants.filter(activo=False).count(),
        'por_vencer': proximos_vencer.count(),
    }

    return render(request, 'panel/dashboard.html', {
        'tenants': tenants,
        'proximos_vencer': proximos_vencer,
        'stats': stats,
    })


@panel_required
def tenant_detalle(request, slug):
    tenant = get_object_or_404(Tenant, slug=slug)
    suscripciones = tenant.suscripciones.select_related('plan').order_by('-fecha_fin')
    planes = Plan.objects.filter(activo=True)

    return render(request, 'panel/tenant_detalle.html', {
        'tenant': tenant,
        'suscripciones': suscripciones,
        'planes': planes,
    })


@panel_required
def tenant_toggle(request, slug):
    tenant = get_object_or_404(Tenant, slug=slug)
    tenant.activo = not tenant.activo
    tenant.save()
    estado = 'activado' if tenant.activo else 'desactivado'
    messages.success(request, f'{tenant.nombre} {estado} correctamente.')
    return redirect('panel:detalle', slug=slug)


@panel_required
def suscripcion_crear(request, slug):
    tenant = get_object_or_404(Tenant, slug=slug)

    if request.method == 'POST':
        plan_id = request.POST.get('plan')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        notas = request.POST.get('notas', '')

        plan = get_object_or_404(Plan, id=plan_id)
        tenant.suscripciones.filter(estado='activa').update(estado='vencida')

        Suscripcion.objects.create(
            tenant=tenant,
            plan=plan,
            estado='activa',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            notas=notas,
        )
        tenant.activo = True
        tenant.save()

        messages.success(request, f'Suscripción creada y {tenant.nombre} activado.')
        return redirect('panel:detalle', slug=slug)

    return redirect('panel:detalle', slug=slug)


@panel_required
def entrar_como_tenant(request, slug):
    """Redirige al superusuario directamente al consultorio."""
    tenant = get_object_or_404(Tenant, slug=slug)
    return redirect(tenant.app_url)