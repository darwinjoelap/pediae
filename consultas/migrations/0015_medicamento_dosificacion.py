# Generated manually — adds pediatric dosage fields to Medicamento

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0014_add_medicamento'),
    ]

    operations = [
        # Hacer indicaciones opcional (blank=True) para el nuevo modelo con tokens
        migrations.AlterField(
            model_name='medicamento',
            name='indicaciones',
            field=models.TextField(
                blank=True,
                verbose_name='Plantilla de indicaciones',
                help_text=(
                    'Texto libre. Inserta variables automáticas con los botones: '
                    '{{DOSIS}}, {{DOSIS_MG}}, {{FRECUENCIA}}, {{DURACION}}, '
                    '{{PRESENTACION}}, {{NOMBRE}}, {{PESO}}'
                ),
            ),
        ),

        # ── Dosificación pediátrica ──────────────────────────────────────────
        migrations.AddField(
            model_name='medicamento',
            name='dosis_mg_kg_min',
            field=models.DecimalField(
                blank=True, null=True, max_digits=7, decimal_places=3,
                verbose_name='Dosis mínima (mg/kg/dosis)',
                help_text='Si no hay rango, usar solo este campo como dosis fija.',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='dosis_mg_kg_max',
            field=models.DecimalField(
                blank=True, null=True, max_digits=7, decimal_places=3,
                verbose_name='Dosis máxima (mg/kg/dosis)',
                help_text='Completar solo si hay rango (leve / severo). Dejar vacío para dosis fija.',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='frecuencia_horas',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Frecuencia (horas)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='duracion_dias',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Duración (días)',
            ),
        ),

        # ── Presentación ─────────────────────────────────────────────────────
        migrations.AddField(
            model_name='medicamento',
            name='presentacion',
            field=models.CharField(
                blank=True, max_length=100,
                verbose_name='Presentación',
                help_text='Ej: susp. 250 mg/5 mL  |  tab. 500 mg  |  gotas 100 mg/mL',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='concentracion_mg',
            field=models.DecimalField(
                blank=True, null=True, max_digits=8, decimal_places=3,
                verbose_name='Concentración (mg)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='volumen_ml',
            field=models.DecimalField(
                blank=True, null=True, max_digits=6, decimal_places=2,
                verbose_name='Volumen base (mL)',
                help_text='mL correspondientes a la concentración indicada. Dejar vacío para tabletas.',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='unidad_resultado',
            field=models.CharField(
                blank=True, max_length=10,
                choices=[
                    ('mL',      'mL (jarabe / gotas)'),
                    ('tableta', 'Tableta / cápsula'),
                    ('mg',      'mg directo'),
                    ('UI',      'Unidades internacionales'),
                    ('gotas',   'Gotas'),
                ],
                verbose_name='Unidad del resultado',
            ),
        ),

        # ── Límites ───────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='medicamento',
            name='dosis_max_absoluta',
            field=models.DecimalField(
                blank=True, null=True, max_digits=8, decimal_places=2,
                verbose_name='Dosis máxima absoluta (mg/dosis)',
                help_text='Techo del adulto. La dosis calculada nunca superará este valor.',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='edad_min_meses',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Edad mínima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='edad_max_meses',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                verbose_name='Edad máxima (meses)',
            ),
        ),
        migrations.AddField(
            model_name='medicamento',
            name='peso_min_kg',
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                verbose_name='Peso mínimo (kg)',
            ),
        ),
    ]
