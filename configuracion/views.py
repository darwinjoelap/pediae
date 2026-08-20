from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from pediae.decorators import tenant_login_required as login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import ConfigConsultorio
from .forms import ConfigConsultorioForm
from consultas.drive import configurar_cloudinary
import cloudinary.uploader


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


@login_required
def editar_config(request):
    if not request.user.es_doctora:
        messages.error(request, 'Solo la doctora puede editar la configuración.')
        return _r(request, '/agenda/')

    tenant = request.tenant
    config, _ = ConfigConsultorio.objects.get_or_create(tenant=tenant)

    if request.method == 'POST':
        form = ConfigConsultorioForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            obj = form.save(commit=False)
            logo_file = request.FILES.get('logo')
            if logo_file:
                configurar_cloudinary()
                resultado = cloudinary.uploader.upload(
                    logo_file,
                    folder=f'ginea/{tenant.slug}/logo',
                    public_id='logo',
                    overwrite=True,
                    resource_type='image',
                )
                obj.logo_public_id = resultado['public_id']
            obj.save()
            messages.success(request, 'Configuración actualizada correctamente.')
            return _r(request, '/configuracion/')
    else:
        form = ConfigConsultorioForm(instance=config)

    return render(request, 'configuracion/editar.html', {
        'form': form,
        'config': config,
    })


# ── Catálogo de vacunas del consultorio ───────────────────────────────────────

def _solo_medico(request):
    if not request.user.es_medico:
        from django.contrib import messages
        messages.error(request, 'Solo el médico puede gestionar el catálogo de vacunas.')
        return True
    return False


@login_required
def catalogo_vacunas(request):
    if _solo_medico(request):
        return _r(request, '/configuracion/')
    from pacientes.models import Vacuna
    from django.db.models import Q
    pai = Vacuna.objects.filter(tenant=None, activa=True).order_by('orden', 'edad_recomendada_meses', 'dosis_numero')
    extras = Vacuna.objects.filter(tenant=request.tenant).order_by('orden', 'edad_recomendada_meses', 'dosis_numero')
    return render(request, 'configuracion/vacunas.html', {
        'pai': pai,
        'extras': extras,
    })


@login_required
def vacuna_nueva(request):
    if _solo_medico(request):
        return _r(request, '/configuracion/')
    from pacientes.models import Vacuna
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        enfermedad = request.POST.get('enfermedad', '').strip()
        dosis_numero = request.POST.get('dosis_numero', 1)
        edad_meses = request.POST.get('edad_recomendada_meses', 0)
        edad_max = request.POST.get('edad_max_meses', '').strip() or None
        orden = request.POST.get('orden', 0)

        if nombre:
            Vacuna.objects.create(
                tenant=request.tenant,
                nombre=nombre,
                enfermedad=enfermedad,
                dosis_numero=int(dosis_numero),
                edad_recomendada_meses=int(edad_meses),
                edad_max_meses=int(edad_max) if edad_max else None,
                es_pai=False,
                activa=True,
                orden=int(orden),
            )
            from django.contrib import messages
            messages.success(request, f'Vacuna "{nombre}" agregada al catálogo.')
        return _r(request, '/configuracion/vacunas/')
    return _r(request, '/configuracion/vacunas/')


@login_required
def vacuna_editar(request, pk):
    if _solo_medico(request):
        return _r(request, '/configuracion/')
    from pacientes.models import Vacuna
    vacuna = get_object_or_404(Vacuna, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        vacuna.nombre = request.POST.get('nombre', vacuna.nombre).strip()
        vacuna.enfermedad = request.POST.get('enfermedad', '').strip()
        vacuna.dosis_numero = int(request.POST.get('dosis_numero', vacuna.dosis_numero))
        vacuna.edad_recomendada_meses = int(request.POST.get('edad_recomendada_meses', vacuna.edad_recomendada_meses))
        edad_max = request.POST.get('edad_max_meses', '').strip()
        vacuna.edad_max_meses = int(edad_max) if edad_max else None
        vacuna.orden = int(request.POST.get('orden', vacuna.orden))
        vacuna.save()
        from django.contrib import messages
        messages.success(request, f'Vacuna "{vacuna.nombre}" actualizada.')
    return _r(request, '/configuracion/vacunas/')


@login_required
def vacuna_toggle(request, pk):
    if _solo_medico(request):
        return _r(request, '/configuracion/')
    from pacientes.models import Vacuna
    vacuna = get_object_or_404(Vacuna, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        vacuna.activa = not vacuna.activa
        vacuna.save()
        estado = 'activada' if vacuna.activa else 'desactivada'
        from django.contrib import messages
        messages.success(request, f'Vacuna "{vacuna.nombre}" {estado}.')
    return _r(request, '/configuracion/vacunas/')


@login_required
def vacuna_eliminar(request, pk):
    if _solo_medico(request):
        return _r(request, '/configuracion/')
    from pacientes.models import Vacuna
    from django.contrib import messages
    vacuna = get_object_or_404(Vacuna, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        nombre = vacuna.nombre
        if vacuna.aplicaciones.exists():
            messages.error(request, f'No se puede eliminar "{nombre}": hay dosis aplicadas a pacientes. Desactívala en su lugar.')
        else:
            vacuna.delete()
            messages.success(request, f'Vacuna "{nombre}" eliminada del catálogo.')
    return _r(request, '/configuracion/vacunas/')