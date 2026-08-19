from ginea.decorators import tenant_login_required as login_required
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