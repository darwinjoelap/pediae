from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0009_consulta_imagenes'),
    ]

    operations = [
        # Nuevos campos
        migrations.AddField(
            model_name='consulta',
            name='tipo_consulta',
            field=models.CharField(
                choices=[
                    ('control_sano', 'Control sano'),
                    ('enfermedad', 'Consulta por enfermedad'),
                    ('seguimiento', 'Seguimiento'),
                ],
                default='control_sano',
                max_length=20,
                verbose_name='Tipo de consulta',
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='talla',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name='Talla / Longitud (cm)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='perimetro_cefalico',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, verbose_name='Perímetro cefálico (cm)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='frecuencia_cardiaca',
            field=models.IntegerField(blank=True, null=True, verbose_name='Frecuencia cardíaca (lpm)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='frecuencia_respiratoria',
            field=models.IntegerField(blank=True, null=True, verbose_name='Frecuencia respiratoria (rpm)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='temperatura',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, verbose_name='Temperatura (°C)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='saturacion_oxigeno',
            field=models.IntegerField(blank=True, null=True, verbose_name='Saturación O₂ (%)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='percentil_peso',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name='Percentil peso/edad (OMS)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='percentil_talla',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name='Percentil talla/edad (OMS)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='percentil_pc',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name='Percentil PC/edad (OMS)'),
        ),
        migrations.AddField(
            model_name='consulta',
            name='clasificacion_nutricional',
            field=models.CharField(
                blank=True,
                choices=[
                    ('desnutricion_severa', 'Desnutrición severa (<p3)'),
                    ('desnutricion', 'Desnutrición (p3-p10)'),
                    ('riesgo_desnutricion', 'Riesgo de desnutrición (p10-p15)'),
                    ('eutrofico', 'Eutrófico (p15-p85)'),
                    ('sobrepeso', 'Sobrepeso (p85-p97)'),
                    ('obesidad', 'Obesidad (>p97)'),
                ],
                max_length=30,
                verbose_name='Clasificación nutricional',
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='desarrollo_psicomotor',
            field=models.TextField(blank=True, verbose_name='Desarrollo psicomotor'),
        ),
        # Eliminar campos ginecológicos
        migrations.RemoveField(model_name='consulta', name='ecografia'),
        migrations.RemoveField(model_name='consulta', name='colposcopia'),
        migrations.RemoveField(model_name='consulta', name='imagenes'),
        migrations.RemoveField(model_name='consulta', name='es_prenatal'),
        migrations.RemoveField(model_name='consulta', name='fpp'),
        migrations.RemoveField(model_name='consulta', name='semanas_gestacion'),
        migrations.RemoveField(model_name='consulta', name='altura_uterina'),
        migrations.RemoveField(model_name='consulta', name='fcf'),
        migrations.RemoveField(model_name='consulta', name='presentacion_fetal'),
        migrations.RemoveField(model_name='consulta', name='edemas'),
        # Actualizar verbose_name de campos que se mantienen
        migrations.AlterField(
            model_name='consulta',
            name='motivo_consulta',
            field=models.TextField(blank=True, verbose_name='Motivo de consulta'),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='diagnostico',
            field=models.TextField(verbose_name='Diagnóstico / Impresión diagnóstica'),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='tratamiento',
            field=models.TextField(verbose_name='Tratamiento / Plan'),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='laboratorio',
            field=models.TextField(blank=True, verbose_name='Exámenes paraclínicos solicitados'),
        ),
    ]
