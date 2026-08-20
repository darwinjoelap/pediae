from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from .models import Paciente


def seccion(titulo):
    return HTML(f'''
        <div class="col-12 mt-4 mb-2">
          <h6 class="fw-bold text-uppercase text-muted border-bottom pb-1"
              style="font-size:0.75rem;letter-spacing:1px;color:#38B8D8!important">
            {titulo}
          </h6>
        </div>
    ''')


NO_CEDULADO_JS = HTML('''
<div class="col-12">
  <script>
  (function() {
    function toggleCedula() {
      var chk = document.getElementById('id_no_cedulado');
      if (!chk) return;
      var cedRow = document.getElementById('cedula-paciente-row');
      var repRow = document.getElementById('representante-row');
      if (chk.checked) {
        if (cedRow) cedRow.style.display = 'none';
        if (repRow) repRow.style.display = '';
      } else {
        if (cedRow) cedRow.style.display = '';
        if (repRow) repRow.style.display = 'none';
      }
    }

    function autofillNombre(filiacion, nombreRep, nombreMadre, nombrePadre) {
      if (filiacion === 'madre' && nombreMadre && !nombreMadre.value) {
        nombreMadre.value = nombreRep;
      } else if (filiacion === 'padre' && nombrePadre && !nombrePadre.value) {
        nombrePadre.value = nombreRep;
      }
    }

    function onFiliacionChange() {
      var sel = document.getElementById('id_filiacion_representante');
      var nombreRep = document.getElementById('id_nombre_representante');
      var nombreMadre = document.getElementById('id_nombre_madre');
      var nombrePadre = document.getElementById('id_nombre_padre');
      var parentescoRow = document.getElementById('parentesco-row');
      if (!sel) return;
      var val = sel.value;
      if (parentescoRow) parentescoRow.style.display = (val === 'otro') ? '' : 'none';
      if (nombreRep && nombreRep.value) autofillNombre(val, nombreRep.value, nombreMadre, nombrePadre);
    }

    document.addEventListener('DOMContentLoaded', function() {
      var chk = document.getElementById('id_no_cedulado');
      if (chk) { toggleCedula(); chk.addEventListener('change', toggleCedula); }
      var sel = document.getElementById('id_filiacion_representante');
      if (sel) {
        onFiliacionChange();
        sel.addEventListener('change', onFiliacionChange);
        var nombreRep = document.getElementById('id_nombre_representante');
        if (nombreRep) {
          nombreRep.addEventListener('input', function() {
            autofillNombre(sel.value, nombreRep.value,
              document.getElementById('id_nombre_madre'),
              document.getElementById('id_nombre_padre'));
          });
        }
      }
    });
  })();
  </script>
</div>
''')

REPRESENTANTE_BLOCK = [
    HTML('<div id="cedula-paciente-row" class="row g-2 mb-2">'),
    Column('cedula', css_class='col-12 col-md-5'),
    HTML('</div>'),
    HTML('<div id="representante-row" class="row g-2 mb-2" style="display:none">'),
    Column('filiacion_representante', css_class='col-12 col-md-3'),
    Column('nombre_representante', css_class='col-12 col-md-5'),
    Column('cedula_representante', css_class='col-12 col-md-4'),
    HTML('<div id="parentesco-row" class="col-12 mt-1" style="display:none">'),
    Column('parentesco_representante', css_class='col-12 col-md-6'),
    HTML('</div>'),
    HTML('</div>'),
]


class PacienteAsistenteForm(forms.ModelForm):
    """Formulario reducido para asistente — datos mínimos para agendar."""
    class Meta:
        model = Paciente
        fields = [
            'nombre_completo', 'sexo', 'no_cedulado', 'cedula',
            'filiacion_representante', 'nombre_representante',
            'cedula_representante', 'parentesco_representante',
            'fecha_nacimiento', 'telefono', 'email', 'contacto_emergencia',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        for f in ['fecha_nacimiento', 'email', 'contacto_emergencia',
                  'cedula', 'cedula_representante', 'nombre_representante',
                  'filiacion_representante', 'parentesco_representante', 'sexo']:
            if f in self.fields:
                self.fields[f].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nombre_completo', css_class='col-12 col-md-7'),
                Column('sexo', css_class='col-6 col-md-2'),
                Column('no_cedulado', css_class='col-6 col-md-3 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            *REPRESENTANTE_BLOCK,
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-4'),
                Column('telefono', css_class='col-12 col-md-4'),
                Column('email', css_class='col-12 col-md-4'),
            ),
            'contacto_emergencia',
            Submit('submit', 'Registrar paciente', css_class='btn btn-primary btn-touch w-100 mt-3'),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class PacienteDoctoraNuevoForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombre_completo', 'sexo', 'no_cedulado', 'cedula',
            'filiacion_representante', 'nombre_representante',
            'cedula_representante', 'parentesco_representante',
            'fecha_nacimiento', 'telefono', 'email', 'contacto_emergencia',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        for f in ['fecha_nacimiento', 'email', 'contacto_emergencia',
                  'cedula', 'cedula_representante', 'nombre_representante',
                  'filiacion_representante', 'parentesco_representante', 'sexo']:
            if f in self.fields:
                self.fields[f].required = False

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nombre_completo', css_class='col-12 col-md-7'),
                Column('sexo', css_class='col-6 col-md-2'),
                Column('no_cedulado', css_class='col-6 col-md-3 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            *REPRESENTANTE_BLOCK,
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-4'),
                Column('telefono', css_class='col-12 col-md-4'),
                Column('email', css_class='col-12 col-md-4'),
            ),
            'contacto_emergencia',
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class PacientePersonalForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombre_completo', 'sexo', 'no_cedulado', 'cedula',
            'filiacion_representante', 'nombre_representante',
            'cedula_representante', 'parentesco_representante',
            'nombre_padre', 'nombre_madre',
            'telefono_representante', 'ocupacion_representante',
            'fecha_nacimiento', 'telefono', 'email',
            'direccion', 'contacto_emergencia', 'seguro_medico',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        optional = [
            'fecha_nacimiento', 'email', 'direccion', 'contacto_emergencia',
            'seguro_medico', 'cedula', 'cedula_representante',
            'nombre_padre', 'nombre_madre', 'nombre_representante',
            'filiacion_representante', 'parentesco_representante',
            'telefono_representante', 'ocupacion_representante', 'sexo',
        ]
        for f in optional:
            if f in self.fields:
                self.fields[f].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            seccion('Datos del paciente'),
            Row(
                Column('nombre_completo', css_class='col-12 col-md-7'),
                Column('sexo', css_class='col-6 col-md-2'),
                Column('no_cedulado', css_class='col-6 col-md-3 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            *REPRESENTANTE_BLOCK,
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-4'),
                Column('telefono', css_class='col-12 col-md-4'),
                Column('email', css_class='col-12 col-md-4'),
            ),
            'direccion',
            Row(
                Column('contacto_emergencia', css_class='col-12 col-md-6'),
                Column('seguro_medico', css_class='col-12 col-md-6'),
            ),
            seccion('Padres / Representante'),
            Row(
                Column('nombre_padre', css_class='col-12 col-md-6'),
                Column('nombre_madre', css_class='col-12 col-md-6'),
            ),
            Row(
                Column('telefono_representante', css_class='col-12 col-md-6'),
                Column('ocupacion_representante', css_class='col-12 col-md-6'),
            ),
            Submit('submit', 'Guardar', css_class='btn btn-primary btn-touch w-100 mt-3'),
        )


class PacienteCompletoForm(forms.ModelForm):
    class Meta:
        model = Paciente
        exclude = ['creado_en', 'actualizado_en', 'tenant']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'direccion': forms.Textarea(attrs={'rows': 2}),
            'alergias': forms.Textarea(attrs={'rows': 2}),
            'enfermedades_cronicas': forms.Textarea(attrs={'rows': 2}),
            'cirugias_previas': forms.Textarea(attrs={'rows': 2}),
            'medicacion_actual': forms.Textarea(attrs={'rows': 2}),
            'antec_embarazo': forms.Textarea(attrs={'rows': 3}),
            'antec_parto': forms.Textarea(attrs={'rows': 3}),
            'antec_neonatal': forms.Textarea(attrs={'rows': 3}),
            'antec_autoinmunes': forms.Textarea(attrs={'rows': 2}),
            'antec_geneticas': forms.Textarea(attrs={'rows': 2}),
            'antec_otros': forms.Textarea(attrs={'rows': 2}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'fecha_nacimiento' in self.fields:
            self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']

        optional = [
            'sexo', 'cedula', 'fecha_nacimiento', 'email', 'direccion',
            'contacto_emergencia', 'seguro_medico',
            'nombre_padre', 'nombre_madre', 'nombre_representante',
            'filiacion_representante', 'parentesco_representante',
            'cedula_representante', 'telefono_representante', 'ocupacion_representante',
            'alergias', 'enfermedades_cronicas', 'cirugias_previas',
            'medicacion_actual', 'grupo_sanguineo',
            'antec_embarazo', 'peso_nacer', 'talla_nacer',
            'antec_parto', 'antec_neonatal',
            'antec_autoinmunes', 'antec_geneticas', 'antec_otros',
            'observaciones',
        ]
        for f in optional:
            if f in self.fields:
                self.fields[f].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            seccion('Datos del paciente'),
            Row(
                Column('nombre_completo', css_class='col-12 col-md-7'),
                Column('sexo', css_class='col-6 col-md-2'),
                Column('no_cedulado', css_class='col-6 col-md-3 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            *REPRESENTANTE_BLOCK,
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-4'),
                Column('telefono', css_class='col-12 col-md-4'),
                Column('email', css_class='col-12 col-md-4'),
            ),
            'direccion',
            Row(
                Column('contacto_emergencia', css_class='col-12 col-md-6'),
                Column('seguro_medico', css_class='col-12 col-md-6'),
            ),
            seccion('Padres / Representante'),
            Row(
                Column('nombre_padre', css_class='col-12 col-md-6'),
                Column('nombre_madre', css_class='col-12 col-md-6'),
            ),
            Row(
                Column('telefono_representante', css_class='col-12 col-md-6'),
                Column('ocupacion_representante', css_class='col-12 col-md-6'),
            ),
            seccion('Antecedentes personales'),
            'alergias',
            'enfermedades_cronicas',
            'cirugias_previas',
            'medicacion_actual',
            Row(
                Column('grupo_sanguineo', css_class='col-6 col-md-3'),
            ),
            seccion('Antecedentes perinatales'),
            'antec_embarazo',
            Row(
                Column('peso_nacer', css_class='col-6 col-md-3'),
                Column('talla_nacer', css_class='col-6 col-md-3'),
            ),
            'antec_parto',
            'antec_neonatal',
            seccion('Antecedentes familiares'),
            Row(
                Column('antec_diabetes', css_class='col-6 col-md-2'),
                Column('antec_hipertension', css_class='col-6 col-md-2'),
                Column('antec_cardiopatias', css_class='col-6 col-md-2'),
                Column('antec_epilepsia', css_class='col-6 col-md-3'),
                Column('antec_asma_atopia', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('antec_autoinmunes', css_class='col-12 col-md-6'),
                Column('antec_geneticas', css_class='col-12 col-md-6'),
            ),
            'antec_otros',
            seccion('Observaciones'),
            'observaciones',
            Submit('submit', 'Guardar ficha', css_class='btn btn-primary btn-touch w-100 mt-4'),
        )
