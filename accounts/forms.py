from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario


class UsuarioCrearForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'username', 'email', 'rol', 'sexo',
                  'especialidad', 'credenciales', 'numero_mpps', 'telefono']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        validate_password(p2)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UsuarioEditarForm(forms.ModelForm):
    # Campos extra para subir firma/sello a Cloudinary (no son campos del modelo)
    firma_upload = forms.ImageField(
        required=False,
        label='Firma digital',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text='PNG con fondo transparente recomendado. Aparece encima de la línea de firma en los PDFs.',
    )
    sello_upload = forms.ImageField(
        required=False,
        label='Sello / Timbre',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text='PNG con fondo transparente recomendado. Aparece al lado de la firma en los PDFs.',
    )
    limpiar_firma = forms.BooleanField(required=False, label='Eliminar firma actual')
    limpiar_sello = forms.BooleanField(required=False, label='Eliminar sello actual')
    banner_upload = forms.ImageField(
        required=False,
        label='Banner de encabezado PDF',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text='Imagen que reemplaza el membrete (logo + datos) en los PDFs cuando el banner está habilitado.',
    )
    limpiar_banner = forms.BooleanField(required=False, label='Eliminar banner actual')

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'rol', 'sexo', 'is_active',
                  'especialidad', 'credenciales', 'numero_mpps', 'telefono', 'usar_banner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].label = 'Usuario activo'

    def save(self, commit=True):
        usuario = super().save(commit=False)

        firma_file = self.cleaned_data.get('firma_upload')
        if firma_file:
            try:
                import cloudinary.uploader
                result = cloudinary.uploader.upload(
                    firma_file,
                    folder='firmas',
                    public_id=f'firma_{usuario.pk}',
                    overwrite=True,
                    resource_type='image',
                )
                usuario.firma_public_id = result['public_id']
            except Exception:
                pass
        elif self.cleaned_data.get('limpiar_firma'):
            usuario.firma_public_id = ''

        sello_file = self.cleaned_data.get('sello_upload')
        if sello_file:
            try:
                import cloudinary.uploader
                result = cloudinary.uploader.upload(
                    sello_file,
                    folder='sellos',
                    public_id=f'sello_{usuario.pk}',
                    overwrite=True,
                    resource_type='image',
                )
                usuario.sello_public_id = result['public_id']
            except Exception:
                pass
        elif self.cleaned_data.get('limpiar_sello'):
            usuario.sello_public_id = ''

        banner_file = self.cleaned_data.get('banner_upload')
        if banner_file:
            try:
                import cloudinary.uploader
                result = cloudinary.uploader.upload(
                    banner_file,
                    folder='banners',
                    public_id=f'banner_{usuario.pk}',
                    overwrite=True,
                    resource_type='image',
                )
                usuario.banner_public_id = result['public_id']
            except Exception:
                pass
        elif self.cleaned_data.get('limpiar_banner'):
            usuario.banner_public_id = ''

        if commit:
            usuario.save()
        return usuario


class CambiarPasswordForm(forms.Form):
    password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        validate_password(p2)
        return p2
