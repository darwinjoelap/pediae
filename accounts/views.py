from django.contrib.auth import authenticate, login, logout
from pediae.decorators import tenant_login_required as login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuario


def _prefix(request):
    tenant = getattr(request, 'tenant', None)
    return f'/t/{tenant.slug}' if tenant else ''


def _r(request, path):
    return redirect(f'{_prefix(request)}{path}')


def login_view(request):
    if request.user.is_authenticated:
        return redirect(f'{_prefix(request)}/agenda/')

    error = False
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            tenant = getattr(request, 'tenant', None)
            if tenant and not user.is_superuser and user.tenant_id != tenant.id:
                error = 'no_pertenece'
            else:
                prefix = f'/t/{tenant.slug}' if tenant else ''
                login(request, user)
                next_url = request.GET.get('next') or f'{prefix}/agenda/'
                return redirect(next_url)
        else:
            error = True

    return render(request, 'accounts/login.html', {
        'form': type('F', (), {'errors': error})(),
        'error_tenant': error == 'no_pertenece',
    })


def logout_view(request):
    if request.method == 'POST':
        partes = request.path.strip('/').split('/')
        slug = partes[1] if len(partes) >= 2 and partes[0] == 't' else None
        logout(request)
        if slug:
            return redirect(f'/t/{slug}/accounts/login/')
        return redirect('/panel/login/')
    return redirect('/')


@login_required
def gestionar_usuarios(request):
    if not request.user.es_medico:
        messages.error(request, 'Solo el médico puede gestionar usuarios.')
        return _r(request, '/agenda/')
    tenant = request.tenant
    usuarios = Usuario.objects.filter(tenant=tenant).exclude(is_superuser=True)
    return render(request, 'accounts/usuarios.html', {'usuarios': usuarios})


@login_required
def crear_usuario(request):
    if not request.user.es_medico:
        messages.error(request, 'Solo el médico puede crear usuarios.')
        return _r(request, '/agenda/')

    from .forms import UsuarioCrearForm
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.tenant = request.tenant
            usuario.save()
            messages.success(request, f'Usuario {usuario.username} creado correctamente.')
            return _r(request, '/accounts/usuarios/')
    else:
        form = UsuarioCrearForm()

    return render(request, 'accounts/usuario_form.html', {
        'form': form, 'titulo': 'Nuevo usuario'
    })


@login_required
def editar_usuario(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'Solo el médico puede editar usuarios.')
        return _r(request, '/agenda/')

    tenant = request.tenant
    usuario = get_object_or_404(Usuario, pk=pk, tenant=tenant)

    from .forms import UsuarioEditarForm, CambiarPasswordForm
    form = UsuarioEditarForm(
        request.POST or None,
        request.FILES or None,
        instance=usuario,
    )
    pass_form = CambiarPasswordForm(request.POST or None)

    if request.method == 'POST':
        if 'cambiar_password' in request.POST:
            if pass_form.is_valid():
                usuario.set_password(pass_form.cleaned_data['password1'])
                usuario.save()
                messages.success(request, 'Contraseña actualizada.')
                return _r(request, '/accounts/usuarios/')
        elif form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado.')
            return _r(request, '/accounts/usuarios/')

    return render(request, 'accounts/usuario_form.html', {
        'form': form,
        'pass_form': pass_form,
        'usuario': usuario,
        'titulo': f'Editar {usuario.username}',
    })