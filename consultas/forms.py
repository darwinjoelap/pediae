from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Field

from .models import Consulta


def seccion(titulo):
    return HTML(f'''
        <div class="col-12 mt-3 mb-1">
          <h6 class="fw-bold text-uppercase text-muted border-bottom pb-1"
              style="font-size:0.75rem;letter-spacing:1px;color:#6f42c1!important">
            {titulo}
          </h6>
        </div>
    ''')


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        exclude = ['paciente', 'cita', 'creado_en', 'tenant', 'medico', 'pagado', 'notas_pago']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'proxima_cita': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fpp': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'motivo_consulta': forms.Textarea(attrs={'rows': 2}),
            'sintomas_actuales': forms.Textarea(attrs={'rows': 2}),
            'examen_fisico': forms.Textarea(attrs={'rows': 3}),
            'ecografia': forms.Textarea(attrs={'rows': 2}),
            'colposcopia': forms.Textarea(attrs={'rows': 2}),
            'imagenes': forms.Textarea(attrs={'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'rows': 2}),
            'tratamiento': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['fecha', 'proxima_cita', 'fpp']:
            if f in self.fields:
                self.fields[f].input_formats = ['%Y-%m-%d']

        optional = [
            'sintomas_actuales', 'examen_fisico', 'ecografia', 'colposcopia',
            'imagenes',
            'proxima_cita', 'observaciones',
            'peso', 'tension_arterial', 'fpp', 'semanas_gestacion',
            'altura_uterina', 'fcf', 'presentacion_fetal', 'edemas', 'lugar',
        ]
        for f in optional:
            if f in self.fields:
                self.fields[f].required = False

        if 'lugar' in self.fields:
            from agenda.models import LugarConsulta
            if tenant:
                self.fields['lugar'].queryset = LugarConsulta.objects.filter(
                    tenant=tenant, activo=True
                )
            else:
                self.fields['lugar'].queryset = LugarConsulta.objects.none()
            self.fields['lugar'].empty_label = '— Sin especificar —'

        self.helper = FormHelper()
        self.helper.layout = Layout(
            seccion('Datos de la consulta'),
            Row(
                Column('fecha', css_class='col-12 col-md-4'),
                Column('lugar', css_class='col-12 col-md-8'),
            ),
            Row(
                Column('peso', css_class='col-6 col-md-3'),
                Column('tension_arterial', css_class='col-6 col-md-3'),
            ),
            'motivo_consulta',
            'sintomas_actuales',
            'examen_fisico',
            'ecografia',
            'colposcopia',
            'imagenes',
            'diagnostico',
            'tratamiento',
            Row(
                Column('proxima_cita', css_class='col-12 col-md-6'),
            ),
            'observaciones',

            seccion('Control prenatal (completar solo si aplica)'),
            Row(
                Column('es_prenatal', css_class='col-12 col-md-2 pt-md-4'),
                Column('semanas_gestacion', css_class='col-6 col-md-2'),
                Column('fpp', css_class='col-12 col-md-4'),
                Column('altura_uterina', css_class='col-6 col-md-2'),
                Column('fcf', css_class='col-6 col-md-2'),
            ),
            Row(
                Column('presentacion_fetal', css_class='col-12 col-md-6'),
                Column('edemas', css_class='col-12 col-md-3 pt-md-4'),
                'laboratorio',
            ),

            Submit('submit', 'Guardar consulta', css_class='btn btn-primary btn-touch w-100 mt-4'),
        )


class AdjuntoForm(forms.Form):
    archivo = forms.FileField(
        label='Seleccionar archivo',
        help_text='Imágenes (JPG, PNG) o PDF. Máximo 10MB.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'archivo',
            Submit('submit', 'Subir archivo', css_class='btn btn-primary btn-touch w-100 mt-3'),
        )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede superar 10MB.')
            tipo = archivo.content_type
            if not (tipo.startswith('image/') or tipo == 'application/pdf'):
                raise forms.ValidationError('Solo se permiten imágenes o PDF.')
        return archivo