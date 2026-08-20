from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Field

from .models import Consulta


def seccion(titulo):
    return HTML(f'''
        <div class="col-12 mt-3 mb-1">
          <h6 class="fw-bold text-uppercase text-muted border-bottom pb-1"
              style="font-size:0.75rem;letter-spacing:1px;color:#2AACA8!important">
            {titulo}
          </h6>
        </div>
    ''')


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        exclude = ['paciente', 'cita', 'creado_en', 'tenant', 'medico',
                   'pagado', 'notas_pago',
                   'percentil_peso', 'percentil_talla', 'percentil_pc',
                   'clasificacion_nutricional']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'proxima_cita': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'motivo_consulta': forms.Textarea(attrs={'rows': 2}),
            'sintomas_actuales': forms.Textarea(attrs={'rows': 2}),
            'examen_fisico': forms.Textarea(attrs={'rows': 3}),
            'desarrollo_psicomotor': forms.Textarea(attrs={'rows': 2}),
            'diagnostico': forms.Textarea(attrs={'rows': 2}),
            'tratamiento': forms.Textarea(attrs={'rows': 3}),
            'laboratorio': forms.Textarea(attrs={'rows': 2}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
            'notas_alimentacion': forms.Textarea(attrs={'rows': 2}),
            'notas_sueno': forms.Textarea(attrs={'rows': 2}),
            'notas_eliminacion': forms.Textarea(attrs={'rows': 2}),
            'control_esfinteres': forms.NullBooleanSelect(),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if 'fecha' in self.fields:
            self.fields['fecha'].input_formats = ['%Y-%m-%d']
        if 'proxima_cita' in self.fields:
            self.fields['proxima_cita'].input_formats = ['%Y-%m-%d']

        optional = [
            'tipo_consulta', 'lugar',
            'peso', 'talla', 'perimetro_cefalico',
            'frecuencia_cardiaca', 'frecuencia_respiratoria',
            'temperatura', 'saturacion_oxigeno', 'tension_arterial',
            'sintomas_actuales', 'examen_fisico', 'desarrollo_psicomotor',
            'laboratorio', 'proxima_cita', 'observaciones',
            # hábitos
            'tipo_alimentacion', 'apetito', 'num_comidas', 'notas_alimentacion',
            'horas_sueno_nocturno', 'num_siestas', 'duracion_siesta', 'notas_sueno',
            'frecuencia_deposiciones', 'consistencia_deposiciones',
            'control_esfinteres', 'notas_eliminacion',
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
                Column('lugar', css_class='col-12 col-md-5'),
                Column('tipo_consulta', css_class='col-12 col-md-3'),
            ),

            seccion('Antropometría'),
            Row(
                Column('peso', css_class='col-6 col-md-3'),
                Column('talla', css_class='col-6 col-md-3'),
                Column('perimetro_cefalico', css_class='col-6 col-md-3'),
            ),

            seccion('Signos vitales'),
            Row(
                Column('frecuencia_cardiaca', css_class='col-6 col-md-3'),
                Column('frecuencia_respiratoria', css_class='col-6 col-md-3'),
                Column('temperatura', css_class='col-6 col-md-3'),
                Column('saturacion_oxigeno', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('tension_arterial', css_class='col-6 col-md-3'),
            ),

            seccion('Clínica'),
            'motivo_consulta',
            'sintomas_actuales',
            'examen_fisico',
            'desarrollo_psicomotor',
            'diagnostico',
            'tratamiento',
            'laboratorio',
            Row(
                Column('proxima_cita', css_class='col-12 col-md-6'),
            ),
            'observaciones',

            seccion('Hábitos — Alimentación'),
            Row(
                Column('tipo_alimentacion', css_class='col-12 col-md-4'),
                Column('apetito', css_class='col-6 col-md-3'),
                Column('num_comidas', css_class='col-6 col-md-2'),
            ),
            'notas_alimentacion',

            seccion('Hábitos — Sueño'),
            Row(
                Column('horas_sueno_nocturno', css_class='col-6 col-md-3'),
                Column('num_siestas', css_class='col-6 col-md-3'),
                Column('duracion_siesta', css_class='col-6 col-md-3'),
            ),
            'notas_sueno',

            seccion('Hábitos — Eliminación'),
            Row(
                Column('frecuencia_deposiciones', css_class='col-12 col-md-4'),
                Column('consistencia_deposiciones', css_class='col-12 col-md-4'),
                Column('control_esfinteres', css_class='col-12 col-md-4'),
            ),
            'notas_eliminacion',

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
