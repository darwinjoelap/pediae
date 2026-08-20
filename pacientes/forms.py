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

    function syncNombreRepresentante() {
      var sel = document.getElementById('id_filiacion_representante');
      var nombreRep = document.getElementById('id_nombre_representante');
      var nombreMadre = document.getElementById('id_nombre_madre');
      var nombrePadre = document.getElementById('id_nombre_padre');
      var parentescoRow = document.getElementById('parentesco-row');
      if (!sel || !nombreRep) return;

      var val = sel.value;

      // Mostrar/ocultar campo parentesco
      if (parentescoRow) {
        parentescoRow.style.display = (val === 'otro') ? '' : 'none';
      }

      // Al cambiar filiacion, autocompletar nombre madre/padre desde representante
      nombreRep.addEventListener('input', function() {
        autofillNombre(sel.value, nombreRep.value, nombreMadre, nombrePadre);
      });
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
      if (parentescoRow) {
        parentescoRow.style.display = (val === 'otro') ? '' : 'none';
      }

      // Al cambiar la filiacion, copiar nombre si el destino esta vacio
      if (nombreRep && nombreRep.value) {
        autofillNombre(val, nombreRep.value, nombreMadre, nombrePadre);
      }
    }

    document.addEventListener('DOMContentLoaded', function() {
      var chk = document.getElementById('id_no_cedulado');
      if (chk) {
        toggleCedula();
        chk.addEventListener('change', toggleCedula);
      }
      syncNombreRepresentante();
      var sel = document.getElementById('id_filiacion_representante');
      if (sel) {
        onFiliacionChange();
        sel.addEventListener('change', onFiliacionChange);
      }
    });
  })();
  </script>
</div>
''')


class PacienteAsistenteForm(forms.ModelForm):
    """Formulario reducido para asistente — solo datos mínimos para agendar."""
    class Meta:
        model = Paciente
        fields = [
            'nombre_completo', 'no_cedulado', 'cedula',
            'filiacion_representante', 'nombre_representante', 'cedula_representante',
            'parentesco_representante',
            'fecha_nacimiento', 'telefono', 'email', 'contacto_emergencia',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'value': ''}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_nacimiento'].required = False
        self.fields['email'].required = False
        self.fields['contacto_emergencia'].required = False
        self.fields['cedula'].required = False
        self.fields['cedula_representante'].required = False
        self.fields['nombre_representante'].required = False
        self.fields['filiacion_representante'].required = False
        self.fields['parentesco_representante'].required = False
        self._set_defaults()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nombre_completo', css_class='col-12 col-md-8'),
                Column('no_cedulado', css_class='col-12 col-md-4 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            HTML('<div id="cedula-paciente-row" class="row g-2 mb-2">'),
            Column('cedula', css_class='col-12'),
            HTML('</div>'),
            HTML('<div id="representante-row" class="row g-2 mb-2" style="display:none">'),
            Column('filiacion_representante', css_class='col-12 col-md-4'),
            Column('nombre_representante', css_class='col-12 col-md-4'),
            Column('cedula_representante', css_class='col-12 col-md-4'),
            HTML('<div id="parentesco-row" class="col-12" style="display:none">'),
            Column('parentesco_representante', css_class='col-12 col-md-6'),
            HTML('</div>'),
            HTML('</div>'),
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-4'),
                Column('telefono', css_class='col-12 col-md-4'),
                Column('email', css_class='col-12 col-md-4'),
            ),
            'contacto_emergencia',
            Submit('submit', 'Registrar paciente', css_class='btn btn-primary btn-touch w-100 mt-3'),
        )

    def _set_defaults(self):
        pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.estado_civil:
            instance.estado_civil = 'soltera'
        if not instance.nivel_instruccion:
            instance.nivel_instruccion = 'universitario'
        if commit:
            instance.save()
        return instance


class PacienteDoctoraNuevoForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombre_completo', 'no_cedulado', 'cedula',
            'filiacion_representante', 'nombre_representante', 'cedula_representante',
            'parentesco_representante',
            'fecha_nacimiento', 'telefono', 'email', 'contacto_emergencia',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'value': ''}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_nacimiento'].required = False
        self.fields['email'].required = False
        self.fields['contacto_emergencia'].required = False
        self.fields['cedula'].required = False
        self.fields['cedula_representante'].required = False
        self.fields['nombre_representante'].required = False
        self.fields['filiacion_representante'].required = False
        self.fields['parentesco_representante'].required = False

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nombre_completo', css_class='col-12 col-md-8'),
                Column('no_cedulado', css_class='col-12 col-md-4 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            HTML('<div id="cedula-paciente-row" class="row g-2 mb-2">'),
            Column('cedula', css_class='col-12'),
            HTML('</div>'),
            HTML('<div id="representante-row" class="row g-2 mb-2" style="display:none">'),
            Column('filiacion_representante', css_class='col-12 col-md-4'),
            Column('nombre_representante', css_class='col-12 col-md-4'),
            Column('cedula_representante', css_class='col-12 col-md-4'),
            HTML('<div id="parentesco-row" class="col-12" style="display:none">'),
            Column('parentesco_representante', css_class='col-12 col-md-6'),
            HTML('</div>'),
            HTML('</div>'),
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-4'),
                Column('telefono', css_class='col-12 col-md-4'),
                Column('email', css_class='col-12 col-md-4'),
            ),
            'contacto_emergencia',
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.estado_civil:
            instance.estado_civil = 'soltera'
        if not instance.nivel_instruccion:
            instance.nivel_instruccion = 'universitario'
        if commit:
            instance.save()
        return instance


class PacientePersonalForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombre_completo', 'no_cedulado', 'cedula',
            'filiacion_representante', 'nombre_representante', 'cedula_representante',
            'parentesco_representante',
            'nombre_padre', 'nombre_madre',
            'fecha_nacimiento', 'telefono', 'email',
            'estado_civil', 'nivel_instruccion', 'ocupacion',
            'direccion', 'contacto_emergencia', 'seguro_medico',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'value': ''}, format='%Y-%m-%d'),
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_nacimiento'].required = False
        self.fields['email'].required = False
        self.fields['ocupacion'].required = False
        self.fields['direccion'].required = False
        self.fields['contacto_emergencia'].required = False
        self.fields['seguro_medico'].required = False
        self.fields['cedula'].required = False
        self.fields['cedula_representante'].required = False
        self.fields['nombre_padre'].required = False
        self.fields['nombre_madre'].required = False
        self.fields['nombre_representante'].required = False
        self.fields['filiacion_representante'].required = False
        self.fields['parentesco_representante'].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            seccion('Datos personales'),
            Row(
                Column('nombre_completo', css_class='col-12 col-md-8'),
                Column('no_cedulado', css_class='col-12 col-md-4 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            HTML('<div id="cedula-paciente-row" class="row g-2 mb-2">'),
            Column('cedula', css_class='col-12 col-md-4'),
            HTML('</div>'),
            HTML('<div id="representante-row" class="row g-2 mb-2" style="display:none">'),
            Column('filiacion_representante', css_class='col-12 col-md-3'),
            Column('nombre_representante', css_class='col-12 col-md-5'),
            Column('cedula_representante', css_class='col-12 col-md-4'),
            HTML('<div id="parentesco-row" class="col-12" style="display:none">'),
            Column('parentesco_representante', css_class='col-12 col-md-6'),
            HTML('</div>'),
            HTML('</div>'),
            seccion('Datos del representante / padres'),
            Row(
                Column('nombre_padre', css_class='col-12 col-md-6'),
                Column('nombre_madre', css_class='col-12 col-md-6'),
            ),
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-3'),
                Column('telefono', css_class='col-12 col-md-3'),
                Column('email', css_class='col-12 col-md-3'),
                Column('estado_civil', css_class='col-12 col-md-3'),
            ),
            Row(
                Column('nivel_instruccion', css_class='col-12 col-md-6'),
                Column('ocupacion', css_class='col-12 col-md-6'),
            ),
            'direccion',
            Row(
                Column('contacto_emergencia', css_class='col-12 col-md-6'),
                Column('seguro_medico', css_class='col-12 col-md-6'),
            ),
            Submit('submit', 'Guardar', css_class='btn btn-primary btn-touch w-100 mt-3'),
        )


class PacienteCompletoForm(forms.ModelForm):
    class Meta:
        model = Paciente
        exclude = ['creado_en', 'actualizado_en', 'tenant']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'value': ''}, format='%Y-%m-%d'),
            'fur': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_ultimo_parto': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'ultima_citologia_fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vih_fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'diu_fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'direccion': forms.Textarea(attrs={'rows': 2}),
            'alergias': forms.Textarea(attrs={'rows': 2}),
            'enfermedades_cronicas': forms.Textarea(attrs={'rows': 2}),
            'cirugias_previas': forms.Textarea(attrs={'rows': 2}),
            'medicacion_actual': forms.Textarea(attrs={'rows': 2}),
            'its_previas': forms.Textarea(attrs={'rows': 2}),
            'menopausia_sintomas': forms.Textarea(attrs={'rows': 2}),
            'metodos_anteriores': forms.Textarea(attrs={'rows': 2}),
            'antec_autoinmunes': forms.Textarea(attrs={'rows': 2}),
            'antec_geneticas': forms.Textarea(attrs={'rows': 2}),
            'ciclo_caracteristicas': forms.Textarea(attrs={'rows': 2}),
            'antec_otros': forms.Textarea(attrs={'rows': 2}),
            'ultima_citologia_hace': forms.TextInput(attrs={'placeholder': 'Ej: hace 2 años, hace 6 meses'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date_fields = [
            'fecha_nacimiento', 'fur', 'fecha_ultimo_parto',
            'ultima_citologia_fecha', 'vih_fecha', 'diu_fecha'
        ]
        for f in date_fields:
            if f in self.fields:
                self.fields[f].input_formats = ['%Y-%m-%d']

        optional = [
            'cedula', 'nombre_padre', 'nombre_madre',
            'nombre_representante', 'cedula_representante',
            'filiacion_representante', 'parentesco_representante',
            'fecha_nacimiento',
            'email', 'ocupacion', 'direccion', 'contacto_emergencia', 'seguro_medico',
            'alergias', 'enfermedades_cronicas', 'cirugias_previas', 'medicacion_actual',
            'grupo_sanguineo', 'antec_autoinmunes', 'antec_geneticas',
            'fur', 'fecha_ultimo_parto', 'ultima_citologia_fecha', 'ultima_citologia_resultado',
            'vih_fecha', 'its_previas', 'inicio_vida_sexual', 'num_parejas',
            'antec_otros', 'ultima_citologia_hace', 'ciclo_caracteristicas',
            'menopausia_edad', 'menopausia_sintomas', 'metodo_anticonceptivo',
            'metodo_tiempo_uso', 'metodos_anteriores', 'diu_fecha', 'diu_tipo', 'observaciones',
        ]
        for f in optional:
            if f in self.fields:
                self.fields[f].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            seccion('Datos personales'),
            Row(
                Column('nombre_completo', css_class='col-12 col-md-8'),
                Column('no_cedulado', css_class='col-12 col-md-4 pt-md-4'),
            ),
            NO_CEDULADO_JS,
            HTML('<div id="cedula-paciente-row" class="row g-2 mb-2">'),
            Column('cedula', css_class='col-12 col-md-4'),
            HTML('</div>'),
            HTML('<div id="representante-row" class="row g-2 mb-2" style="display:none">'),
            Column('filiacion_representante', css_class='col-12 col-md-3'),
            Column('nombre_representante', css_class='col-12 col-md-5'),
            Column('cedula_representante', css_class='col-12 col-md-4'),
            HTML('<div id="parentesco-row" class="col-12" style="display:none">'),
            Column('parentesco_representante', css_class='col-12 col-md-6'),
            HTML('</div>'),
            HTML('</div>'),
            seccion('Datos del representante / padres'),
            Row(
                Column('nombre_padre', css_class='col-12 col-md-6'),
                Column('nombre_madre', css_class='col-12 col-md-6'),
            ),
            Row(
                Column('fecha_nacimiento', css_class='col-12 col-md-3'),
                Column('telefono', css_class='col-12 col-md-3'),
                Column('email', css_class='col-12 col-md-3'),
                Column('estado_civil', css_class='col-12 col-md-3'),
            ),
            Row(
                Column('nivel_instruccion', css_class='col-12 col-md-6'),
                Column('ocupacion', css_class='col-12 col-md-6'),
            ),
            'direccion',
            Row(
                Column('contacto_emergencia', css_class='col-12 col-md-6'),
                Column('seguro_medico', css_class='col-12 col-md-6'),
            ),
            seccion('Antecedentes personales'),
            'alergias', 'enfermedades_cronicas', 'cirugias_previas', 'medicacion_actual',
            Row(
                Column('grupo_sanguineo', css_class='col-6 col-md-3'),
                Column('tabaquismo', css_class='col-6 col-md-3 pt-md-4'),
                Column('alcoholismo', css_class='col-6 col-md-3 pt-md-4'),
                Column('transfusiones', css_class='col-6 col-md-3 pt-md-4'),
            ),
            seccion('Antecedentes familiares'),
            Row(
                Column('antec_cancer_mama', css_class='col-6 col-md-3'),
                Column('antec_cancer_cuello', css_class='col-6 col-md-3'),
                Column('antec_diabetes', css_class='col-6 col-md-3'),
                Column('antec_hipertension', css_class='col-6 col-md-3'),
            ),
            Row(
                Column('antec_autoinmunes', css_class='col-12 col-md-6'),
                Column('antec_geneticas', css_class='col-12 col-md-6'),
            ),
            'antec_otros',
            seccion('Historia gineco-obstétrica'),
            Row(
                Column('menarquia', css_class='col-6 col-md-3'),
                Column('ciclo_dias', css_class='col-6 col-md-3'),
                Column('ciclo_regular', css_class='col-6 col-md-3 pt-md-4'),
                Column('fur', css_class='col-6 col-md-3'),
            ),
            'ciclo_caracteristicas',
            Row(
                Column('gestas', css_class='col-3'),
                Column('partos', css_class='col-3'),
                Column('cesareas', css_class='col-3'),
                Column('abortos', css_class='col-3'),
            ),
            Row(
                Column('fecha_ultimo_parto', css_class='col-12 col-md-4'),
                Column('ultima_citologia_fecha', css_class='col-12 col-md-4'),
                Column('ultima_citologia_resultado', css_class='col-12 col-md-4'),
            ),
            Row(
                Column('ultima_citologia_hace', css_class='col-12 col-md-6'),
                HTML('<div class="col-12 col-md-6 d-flex align-items-center"><small class="text-muted pt-2">Si no recuerda la fecha exacta, escribe el tiempo aproximado en el campo de la izquierda</small></div>'),
            ),
            Row(
                Column('vph_diagnostico', css_class='col-6 col-md-3'),
                Column('vph_vacuna', css_class='col-6 col-md-3'),
                Column('vih_resultado', css_class='col-12 col-md-3'),
                Column('vih_fecha', css_class='col-12 col-md-3'),
            ),
            'its_previas',
            Row(
                Column('inicio_vida_sexual', css_class='col-6 col-md-3'),
                Column('num_parejas', css_class='col-6 col-md-3'),
                Column('dispareunia', css_class='col-6 col-md-3 pt-md-4'),
            ),
            Row(
                Column('menopausia', css_class='col-6 col-md-3 pt-md-4'),
                Column('menopausia_edad', css_class='col-6 col-md-3'),
                Column('menopausia_sintomas', css_class='col-12 col-md-6'),
            ),
            seccion('Planificación familiar'),
            Row(
                Column('metodo_anticonceptivo', css_class='col-12 col-md-6'),
                Column('metodo_tiempo_uso', css_class='col-12 col-md-6'),
            ),
            'metodos_anteriores',
            Row(
                Column('deseo_embarazo', css_class='col-6 col-md-3 pt-md-4'),
                Column('ligadura', css_class='col-6 col-md-3 pt-md-4'),
                Column('diu_tipo', css_class='col-12 col-md-3'),
                Column('diu_fecha', css_class='col-12 col-md-3'),
            ),
            seccion('Observaciones'),
            'observaciones',
            Submit('submit', 'Guardar ficha', css_class='btn btn-primary btn-touch w-100 mt-4'),
        )
