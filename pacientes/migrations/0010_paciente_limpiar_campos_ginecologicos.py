from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0009_paciente_sexo'),
    ]

    operations = [
        # ── Eliminar campos ginecológicos / de adulto ────────────────────────
        migrations.RemoveField(model_name='paciente', name='estado_civil'),
        migrations.RemoveField(model_name='paciente', name='nivel_instruccion'),
        migrations.RemoveField(model_name='paciente', name='ocupacion'),
        migrations.RemoveField(model_name='paciente', name='tabaquismo'),
        migrations.RemoveField(model_name='paciente', name='alcoholismo'),
        migrations.RemoveField(model_name='paciente', name='transfusiones'),
        # Historia gineco-obstétrica
        migrations.RemoveField(model_name='paciente', name='menarquia'),
        migrations.RemoveField(model_name='paciente', name='ciclo_dias'),
        migrations.RemoveField(model_name='paciente', name='ciclo_regular'),
        migrations.RemoveField(model_name='paciente', name='fur'),
        migrations.RemoveField(model_name='paciente', name='gestas'),
        migrations.RemoveField(model_name='paciente', name='partos'),
        migrations.RemoveField(model_name='paciente', name='cesareas'),
        migrations.RemoveField(model_name='paciente', name='abortos'),
        migrations.RemoveField(model_name='paciente', name='fecha_ultimo_parto'),
        migrations.RemoveField(model_name='paciente', name='ultima_citologia_fecha'),
        migrations.RemoveField(model_name='paciente', name='ultima_citologia_resultado'),
        migrations.RemoveField(model_name='paciente', name='vph_diagnostico'),
        migrations.RemoveField(model_name='paciente', name='vph_vacuna'),
        migrations.RemoveField(model_name='paciente', name='vih_resultado'),
        migrations.RemoveField(model_name='paciente', name='vih_fecha'),
        migrations.RemoveField(model_name='paciente', name='its_previas'),
        migrations.RemoveField(model_name='paciente', name='inicio_vida_sexual'),
        migrations.RemoveField(model_name='paciente', name='num_parejas'),
        migrations.RemoveField(model_name='paciente', name='dispareunia'),
        migrations.RemoveField(model_name='paciente', name='menopausia'),
        migrations.RemoveField(model_name='paciente', name='menopausia_edad'),
        migrations.RemoveField(model_name='paciente', name='menopausia_sintomas'),
        # Planificación familiar
        migrations.RemoveField(model_name='paciente', name='metodo_anticonceptivo'),
        migrations.RemoveField(model_name='paciente', name='metodo_tiempo_uso'),
        migrations.RemoveField(model_name='paciente', name='metodos_anteriores'),
        migrations.RemoveField(model_name='paciente', name='deseo_embarazo'),
        migrations.RemoveField(model_name='paciente', name='diu_fecha'),
        migrations.RemoveField(model_name='paciente', name='diu_tipo'),
        migrations.RemoveField(model_name='paciente', name='ligadura'),
        # Antecedentes familiares ginecológicos
        migrations.RemoveField(model_name='paciente', name='antec_cancer_mama'),
        migrations.RemoveField(model_name='paciente', name='antec_cancer_cuello'),

        # ── Agregar campos pediátricos ───────────────────────────────────────
        migrations.AddField(
            model_name='paciente',
            name='telefono_representante',
            field=models.CharField(blank=True, max_length=20, verbose_name='Teléfono del representante'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='ocupacion_representante',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ocupación del representante'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_embarazo',
            field=models.TextField(
                blank=True,
                verbose_name='Antecedentes del embarazo',
                help_text='Patologías maternas, control prenatal, exposición a riesgos',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_parto',
            field=models.TextField(
                blank=True,
                verbose_name='Antecedentes del parto / nacimiento',
                help_text='Vía de parto, edad gestacional, APGAR, peso y talla al nacer',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_neonatal',
            field=models.TextField(
                blank=True,
                verbose_name='Período neonatal',
                help_text='Estadía en retén, ictericia, lactancia, tamiz neonatal',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_cardiopatias',
            field=models.BooleanField(default=False, verbose_name='Antec. familiar cardiopatías'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_epilepsia',
            field=models.BooleanField(default=False, verbose_name='Antec. familiar epilepsia'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_asma_atopia',
            field=models.BooleanField(default=False, verbose_name='Antec. familiar asma / atopía'),
        ),
    ]
