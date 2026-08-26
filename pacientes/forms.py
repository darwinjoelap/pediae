import re
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from .models import Paciente


def _limpiar_tel(valor):
    """Quita todo lo que no sea dígito o '+' — elimina invisibles Unicode, guiones, espacios, etc."""
    return re.sub(r'[^\d+]', '', valor or '')


class TelefonoCleanMixin:
    """Mixin que limpia los campos de teléfono antes de validar."""
    def clean_telefono(self):
        return _limpiar_tel(self.cleaned_data.get('telefono', ''))

    def clean_telefono_representante(self):
        return _limpiar_tel(self.cleaned_data.get('telefono_representante', ''))


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


class PacienteAsistenteForm(TelefonoCleanMixin, forms.ModelForm):
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


class PacienteDoctoraNuevoForm(TelefonoCleanMixin, forms.ModelForm):
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


class PacientePersonalForm(TelefonoCleanMixin, forms.ModelForm):
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


class PacienteCompletoForm(TelefonoCleanMixin, forms.ModelForm):
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
            'antec_embarazo': forms.Textarea(attrs={'rows': 2}),
            'antec_parto': forms.Textarea(attrs={'rows': 2}),
            'antec_neonatal': forms.Textarea(attrs={'rows': 2}),
            'antec_alimentacion': forms.Textarea(attrs={'rows': 2}),
            'antec_desarrollo': forms.Textarea(attrs={'rows': 2}),
            'antec_autoinmunes': forms.Textarea(attrs={'rows': 2}),
            'antec_geneticas': forms.Textarea(attrs={'rows': 2}),
            'antec_otros': forms.Textarea(attrs={'rows': 2}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'complicacion_embarazo_otra': forms.TextInput(),
            'indicacion_cesarea': forms.TextInput(),
            'neonatal_otra_complicacion': forms.TextInput(),
            'prueba_talon_detalle': forms.TextInput(),
            'nombre_formula': forms.TextInput(),
            'alimentacion_actual_detalle': forms.TextInput(),
            'desarrollo_area_afectada': forms.TextInput(),
            'esfinter_vesical_edad': forms.TextInput(),
            'esfinter_anal_edad': forms.TextInput(),
            'traumatismos_detalle': forms.TextInput(),
            'exantematicas_detalle': forms.TextInput(),
            'mascotas_tipo': forms.TextInput(),
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
            'edad_madre', 'ocupacion_madre', 'edad_padre', 'ocupacion_padre',
            'alergias', 'enfermedades_cronicas', 'cirugias_previas',
            'medicacion_actual', 'grupo_sanguineo',
            'antec_embarazo', 'peso_nacer', 'talla_nacer',
            'antec_parto', 'antec_neonatal',
            'antec_alimentacion', 'antec_desarrollo',
            'antec_autoinmunes', 'antec_geneticas', 'antec_otros',
            'observaciones',
            # Sección 2 estructurado
            'edad_materna_embarazo', 'numero_gestacion', 'control_prenatal',
            'num_consultas_prenatales', 'complicacion_embarazo_otra',
            'semanas_gestacion', 'via_parto', 'indicacion_cesarea',
            'complicaciones_neonatales', 'neonatal_otra_complicacion',
            'onfalorrexis', 'prueba_talon', 'prueba_talon_detalle',
            # Sección 3 estructurado
            'lme', 'lme_meses', 'uso_formula', 'nombre_formula',
            'causa_formula', 'alimentacion_actual', 'alimentacion_actual_detalle',
            # Sección 4 estructurado
            'desarrollo_psicomotor_adecuado', 'desarrollo_area_afectada',
            'esfinter_vesical_logrado', 'esfinter_vesical_edad',
            'esfinter_anal_logrado', 'esfinter_anal_edad',
            # Sección 6 estructurado
            'traumatismos', 'traumatismos_detalle',
            'enfermedades_exantematicas', 'exantematicas_detalle',
            # Sección 7 estructurado
            'antec_oncologico_rama',
            # Sección 8
            'patron_sueno', 'patron_evacuacion', 'patron_miccion',
            'tabaquismo_pasivo', 'agua_consumo', 'mascotas', 'mascotas_tipo',
        ]
        for f in optional:
            if f in self.fields:
                self.fields[f].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            # ── 1. Ficha de identificación ────────────────────────────────────
            seccion('1. Ficha de identificación'),
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
            Row(
                Column('grupo_sanguineo', css_class='col-6 col-md-3'),
            ),
            # ── Padres ────────────────────────────────────────────────────────
            seccion('Padres'),
            Row(
                Column('nombre_padre', css_class='col-12 col-md-5'),
                Column('edad_padre', css_class='col-6 col-md-2'),
                Column('ocupacion_padre', css_class='col-6 col-md-5'),
            ),
            Row(
                Column('nombre_madre', css_class='col-12 col-md-5'),
                Column('edad_madre', css_class='col-6 col-md-2'),
                Column('ocupacion_madre', css_class='col-6 col-md-5'),
            ),
            Row(
                Column('telefono_representante', css_class='col-12 col-md-6'),
                Column('ocupacion_representante', css_class='col-12 col-md-6'),
            ),
            # ── 2. Antecedentes prenatales / perinatales / neonatales ─────────
            seccion('2. Antecedentes prenatales – perinatales – neonatales'),
            Row(
                Column('edad_materna_embarazo', css_class='col-6 col-md-3'),
                Column('numero_gestacion', css_class='col-6 col-md-3'),
                Column('semanas_gestacion', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('control_prenatal', css_class='col-6 col-md-3'),
                Column('num_consultas_prenatales', css_class='col-6 col-md-3'),
            ),
            HTML('<div class="col-12 mt-2 mb-1"><small class="text-muted fw-semibold">Complicaciones en el embarazo</small></div>'),
            Row(
                Column('complicacion_oligoamnios', css_class='col-6 col-md-2'),
                Column('complicacion_preeclampsia', css_class='col-6 col-md-2'),
                Column('complicacion_infecciones', css_class='col-6 col-md-3'),
                Column('complicacion_embarazo_otra', css_class='col-12 col-md-5'),
            ),
            Row(
                Column('via_parto', css_class='col-6 col-md-4'),
                Column('indicacion_cesarea', css_class='col-12 col-md-8'),
            ),
            Row(
                Column('peso_nacer', css_class='col-6 col-md-3'),
                Column('talla_nacer', css_class='col-6 col-md-3'),
            ),
            HTML('<div class="col-12 mt-2 mb-1"><small class="text-muted fw-semibold">Período neonatal (primeros 28 días)</small></div>'),
            Row(
                Column('complicaciones_neonatales', css_class='col-12 col-md-3'),
                Column('neonatal_ictericia', css_class='col-6 col-md-2'),
                Column('neonatal_sepsis', css_class='col-6 col-md-2'),
                Column('neonatal_dificultad_respiratoria', css_class='col-6 col-md-2'),
                Column('neonatal_otra_complicacion', css_class='col-12 col-md-3'),
            ),
            Row(
                Column('onfalorrexis', css_class='col-12 col-md-4'),
                Column('prueba_talon', css_class='col-12 col-md-4'),
                Column('prueba_talon_detalle', css_class='col-12 col-md-4'),
            ),
            HTML('<div class="col-12 mt-2 mb-1"><small class="text-muted fw-semibold">Notas adicionales (campo libre)</small></div>'),
            Row(
                Column('antec_embarazo', css_class='col-12 col-md-4'),
                Column('antec_parto', css_class='col-12 col-md-4'),
                Column('antec_neonatal', css_class='col-12 col-md-4'),
            ),
            # ── 3. Alimentación ───────────────────────────────────────────────
            seccion('3. Alimentación y nutrición'),
            Row(
                Column('lme', css_class='col-6 col-md-3'),
                Column('lme_meses', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('uso_formula', css_class='col-6 col-md-3'),
                Column('nombre_formula', css_class='col-12 col-md-5'),
                Column('causa_formula', css_class='col-12 col-md-4'),
            ),
            Row(
                Column('alimentacion_actual', css_class='col-12 col-md-5'),
                Column('alimentacion_actual_detalle', css_class='col-12 col-md-7'),
            ),
            'antec_alimentacion',
            # ── 4. Desarrollo psicomotor ──────────────────────────────────────
            seccion('4. Desarrollo psicomotor e hitos madurativos'),
            Row(
                Column('desarrollo_psicomotor_adecuado', css_class='col-12 col-md-4'),
                Column('desarrollo_area_afectada', css_class='col-12 col-md-8'),
            ),
            Row(
                Column('esfinter_vesical_logrado', css_class='col-6 col-md-3'),
                Column('esfinter_vesical_edad', css_class='col-6 col-md-3'),
                Column('esfinter_anal_logrado', css_class='col-6 col-md-3'),
                Column('esfinter_anal_edad', css_class='col-6 col-md-3'),
            ),
            'antec_desarrollo',
            # ── 6. Antecedentes patológicos personales ────────────────────────
            seccion('6. Antecedentes patológicos personales'),
            'cirugias_previas',
            'alergias',
            Row(
                Column('traumatismos', css_class='col-6 col-md-3'),
                Column('traumatismos_detalle', css_class='col-12 col-md-9'),
            ),
            Row(
                Column('enfermedades_exantematicas', css_class='col-6 col-md-3'),
                Column('exantematicas_detalle', css_class='col-12 col-md-9'),
            ),
            'enfermedades_cronicas',
            'medicacion_actual',
            # ── 7. Antecedentes familiares ────────────────────────────────────
            seccion('7. Antecedentes familiares'),
            Row(
                Column('antec_diabetes', css_class='col-6 col-md-2'),
                Column('antec_hipertension', css_class='col-6 col-md-2'),
                Column('antec_cardiopatias', css_class='col-6 col-md-2'),
                Column('antec_epilepsia', css_class='col-6 col-md-3'),
                Column('antec_asma_atopia', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('antec_oncologico', css_class='col-6 col-md-3'),
                Column('antec_oncologico_rama', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('antec_autoinmunes', css_class='col-12 col-md-6'),
                Column('antec_geneticas', css_class='col-12 col-md-6'),
            ),
            'antec_otros',
            # ── 8. Hábitos psicobiológicos y entorno ──────────────────────────
            seccion('8. Hábitos psicobiológicos y entorno socio-ambiental'),
            Row(
                Column('patron_sueno', css_class='col-12 col-md-4'),
                Column('patron_evacuacion', css_class='col-12 col-md-4'),
                Column('patron_miccion', css_class='col-12 col-md-4'),
            ),
            Row(
                Column('tabaquismo_pasivo', css_class='col-6 col-md-3'),
                Column('agua_consumo', css_class='col-12 col-md-4'),
                Column('mascotas', css_class='col-6 col-md-2'),
                Column('mascotas_tipo', css_class='col-12 col-md-3'),
            ),
            # ── Observaciones ─────────────────────────────────────────────────
            seccion('Observaciones'),
            'observaciones',
            Submit('submit', 'Guardar ficha', css_class='btn btn-primary btn-touch w-100 mt-4'),
        )
