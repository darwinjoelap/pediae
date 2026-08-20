from django import forms
from .models import ConfigConsultorio


class ConfigConsultorioForm(forms.ModelForm):
    logo = forms.ImageField(required=False, label='Logo del consultorio',
        help_text='PNG o JPG recomendado. Se guardará en Cloudinary.')

    class Meta:
        model = ConfigConsultorio
        fields = [
            'nombre_consultorio', 'nombre_medico', 'especialidad',
            'direccion', 'telefono', 'email',
            'whatsapp_numero', 'whatsapp_mensaje',
            'color_primario', 'color_sidebar',
        ]
        widgets = {
            'whatsapp_mensaje': forms.Textarea(attrs={'rows': 3}),
            'direccion': forms.Textarea(attrs={'rows': 2}),
            'color_primario': forms.TextInput(attrs={'type': 'color'}),
            'color_sidebar': forms.TextInput(attrs={'type': 'color'}),
        }
