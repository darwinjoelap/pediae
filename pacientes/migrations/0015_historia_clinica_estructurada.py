from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0014_paciente_antec_alimentacion_and_more'),
    ]

    operations = [
        # Sección 1 – datos adicionales de padres
        migrations.AddField(
            model_name='paciente',
            name='edad_madre',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Edad de la madre (años)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='ocupacion_madre',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ocupación de la madre'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='edad_padre',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Edad del padre (años)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='ocupacion_padre',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ocupación del padre'),
        ),
        # Sección 2 – perinatales estructurado
        migrations.AddField(
            model_name='paciente',
            name='edad_materna_embarazo',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Edad materna al embarazo (años)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='numero_gestacion',
            field=models.PositiveSmallIntegerField(blank=True, null=True, help_text='Ej: 1 = primera gestación', verbose_name='N° de gestación'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='control_prenatal',
            field=models.BooleanField(blank=True, null=True, verbose_name='Control prenatal'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='num_consultas_prenatales',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='N° de consultas prenatales'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='complicacion_oligoamnios',
            field=models.BooleanField(default=False, verbose_name='Oligoamnios'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='complicacion_preeclampsia',
            field=models.BooleanField(default=False, verbose_name='Preeclampsia'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='complicacion_infecciones',
            field=models.BooleanField(default=False, verbose_name='Infecciones durante embarazo'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='complicacion_embarazo_otra',
            field=models.CharField(blank=True, max_length=200, verbose_name='Otra complicación en el embarazo'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='semanas_gestacion',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Semanas de gestación al nacer'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='via_parto',
            field=models.CharField(blank=True, choices=[('vaginal', 'Vaginal'), ('cesarea', 'Cesárea')], max_length=10, verbose_name='Vía de resolución del parto'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='indicacion_cesarea',
            field=models.CharField(blank=True, max_length=200, verbose_name='Indicación de cesárea'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='complicaciones_neonatales',
            field=models.BooleanField(blank=True, null=True, verbose_name='Presentó complicaciones neonatales'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='neonatal_ictericia',
            field=models.BooleanField(default=False, verbose_name='Ictericia neonatal'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='neonatal_sepsis',
            field=models.BooleanField(default=False, verbose_name='Sepsis neonatal'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='neonatal_dificultad_respiratoria',
            field=models.BooleanField(default=False, verbose_name='Dificultad respiratoria neonatal'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='neonatal_otra_complicacion',
            field=models.CharField(blank=True, max_length=200, verbose_name='Otra complicación neonatal'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='onfalorrexis',
            field=models.CharField(blank=True, choices=[('normal', 'Normal / Sin complicaciones'), ('complicada', 'Alterada / Complicada')], max_length=12, verbose_name='Onfalorrexis (caída del cordón umbilical)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='prueba_talon',
            field=models.CharField(blank=True, choices=[('normal', 'Sin alteraciones (Normal)'), ('alterada', 'Alterada / En estudio')], max_length=10, verbose_name='Prueba del talón'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='prueba_talon_detalle',
            field=models.CharField(blank=True, max_length=300, verbose_name='Detalle prueba del talón alterada'),
        ),
        # Sección 3 – alimentación estructurado
        migrations.AddField(
            model_name='paciente',
            name='lme',
            field=models.BooleanField(blank=True, null=True, verbose_name='Lactancia materna exclusiva (LME)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='lme_meses',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='LME hasta (meses)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='uso_formula',
            field=models.BooleanField(blank=True, null=True, verbose_name='Uso de fórmulas o leches especiales'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nombre_formula',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nombre de fórmula empleada'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='causa_formula',
            field=models.CharField(blank=True, choices=[('evacuaciones', 'Dificultad en evacuaciones'), ('estimulacion', 'Necesidad de estimulación'), ('alergia', 'Alergia'), ('otra', 'Otra')], max_length=15, verbose_name='Causa del uso de fórmula'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='alimentacion_actual',
            field=models.CharField(blank=True, choices=[('completa', 'Dieta completa y variada acorde a la edad'), ('selectiva', 'Dieta selectiva / Restringida')], max_length=10, verbose_name='Alimentación actual'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='alimentacion_actual_detalle',
            field=models.CharField(blank=True, max_length=300, verbose_name='Detalle dieta selectiva/restringida'),
        ),
        # Sección 4 – desarrollo psicomotor estructurado
        migrations.AddField(
            model_name='paciente',
            name='desarrollo_psicomotor_adecuado',
            field=models.BooleanField(blank=True, null=True, verbose_name='Desarrollo neuromotor acorde a la edad'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='desarrollo_area_afectada',
            field=models.CharField(blank=True, help_text='Ej: Motor grueso, Motor fino, Lenguaje, Social-afectivo', max_length=100, verbose_name='Área de desarrollo afectada'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='esfinter_vesical_logrado',
            field=models.BooleanField(blank=True, null=True, verbose_name='Control esfínter vesical (micción) logrado'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='esfinter_vesical_edad',
            field=models.CharField(blank=True, max_length=30, verbose_name='Edad logro control vesical'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='esfinter_anal_logrado',
            field=models.BooleanField(blank=True, null=True, verbose_name='Control esfínter anal (evacuación) logrado'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='esfinter_anal_edad',
            field=models.CharField(blank=True, max_length=30, verbose_name='Edad logro control anal'),
        ),
        # Sección 6 – patológicos adicionales
        migrations.AddField(
            model_name='paciente',
            name='traumatismos',
            field=models.BooleanField(blank=True, null=True, verbose_name='Traumatismos / Accidentes'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='traumatismos_detalle',
            field=models.CharField(blank=True, max_length=300, verbose_name='Detalle de traumatismos'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='enfermedades_exantematicas',
            field=models.BooleanField(blank=True, null=True, verbose_name='Enfermedades exantemáticas'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='exantematicas_detalle',
            field=models.CharField(blank=True, help_text='Varicela, Sarampión, Rubéola, etc.', max_length=200, verbose_name='Detalle enfermedades exantemáticas'),
        ),
        # Sección 7 – familiares oncológico
        migrations.AddField(
            model_name='paciente',
            name='antec_oncologico',
            field=models.BooleanField(default=False, verbose_name='Antec. familiar patología oncológica'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='antec_oncologico_rama',
            field=models.CharField(blank=True, choices=[('materna', 'Materna'), ('paterna', 'Paterna'), ('ambas', 'Ambas')], max_length=8, verbose_name='Rama familiar oncológica'),
        ),
        # Sección 8 – hábitos y entorno
        migrations.AddField(
            model_name='paciente',
            name='patron_sueno',
            field=models.CharField(blank=True, choices=[('tranquilo', 'Tranquilo, reparador y conservado'), ('alterado', 'Alterado / Trastorno del sueño')], max_length=10, verbose_name='Patrón de sueño'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='patron_evacuacion',
            field=models.CharField(blank=True, choices=[('normal', 'Normal / Continente'), ('estrenimiento', 'Estreñimiento'), ('encopresis', 'Encopresis (incontinencia fecal)')], max_length=15, verbose_name='Patrón de evacuación'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='patron_miccion',
            field=models.CharField(blank=True, choices=[('normal', 'Normal / Continente'), ('enuresis_diurna', 'Enuresis diurna'), ('enuresis_nocturna', 'Enuresis nocturna')], max_length=18, verbose_name='Patrón de micción'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='tabaquismo_pasivo',
            field=models.BooleanField(blank=True, null=True, verbose_name='Exposición a humo de tabaco (tabaquismo pasivo)'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='agua_consumo',
            field=models.CharField(blank=True, choices=[('hervida', 'Hervida'), ('filtrada', 'Filtrada'), ('embotellada', 'Embotellada'), ('tuberia', 'Directa de tubería')], max_length=12, verbose_name='Tratamiento del agua de consumo'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='mascotas',
            field=models.BooleanField(blank=True, null=True, verbose_name='Mascotas en el hogar'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='mascotas_tipo',
            field=models.CharField(blank=True, max_length=100, verbose_name='Tipo de mascotas'),
        ),
    ]
