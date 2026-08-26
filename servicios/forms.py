from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Servicio, TasaCambio


class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['tasa']
        widgets = {
            'tasa': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ej: 46.50'}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio_usd', 'costo_adquisicion_usd', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
            'precio_usd': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'costo_adquisicion_usd': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00 (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Guardar servicio', css_class='btn btn-primary btn-touch w-100 mt-3'))