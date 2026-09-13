from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0016_merge_medicamento_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicamento',
            name='modo_calculo',
            field=models.CharField(
                choices=[
                    ('peso', 'Por peso (mg/kg)'),
                    ('fija', 'Dosis fija (puffs, inhalaciones…)'),
                    ('edad', 'Por rango de edad'),
                ],
                default='peso',
                max_length=10,
                verbose_name='Modo de cálculo',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='unidad_dosis_kg',
            field=models.CharField(
                blank=True,
                choices=[
                    ('mg',  'mg/kg'),
                    ('mcg', 'mcg/kg'),
                    ('UI',  'UI/kg'),
                    ('g',   'g/kg'),
                ],
                default='mg',
                max_length=5,
                verbose_name='Unidad de dosis/kg',
            ),
        ),
        # ── Rango 1 ──────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='medicamento',
            name='rango1_edad_min',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Rango 1 - edad mínima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='rango1_edad_max',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Rango 1 - edad máxima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='rango1_dosis',
            field=models.CharField(
                blank=True, max_length=100,
                verbose_name='Rango 1 - dosis',
                help_text='Ej: 1/2 sobre, 5 mL, 1 comprimido',
            ),
        ),
        # ── Rango 2 ──────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='medicamento',
            name='rango2_edad_min',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Rango 2 - edad mínima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='rango2_edad_max',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Rango 2 - edad máxima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='rango2_dosis',
            field=models.CharField(
                blank=True, max_length=100,
                verbose_name='Rango 2 - dosis',
            ),
        ),
        # ── Rango 3 ──────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='medicamento',
            name='rango3_edad_min',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Rango 3 - edad mínima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='rango3_edad_max',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Rango 3 - edad máxima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='rango3_dosis',
            field=models.CharField(
                blank=True, max_length=100,
                verbose_name='Rango 3 - dosis',
            ),
        ),
    ]
