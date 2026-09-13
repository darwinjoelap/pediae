from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Amplía unidad_dosis_kg para soportar unidades directas (mL, gotas, tableta,
    sobre, puff, aplicacion) además de las unidades de masa ya existentes.
    Solo cambia max_length de 5 → 10 y actualiza las choices.
    """

    dependencies = [
        ('consultas', '0017_medicamento_modo_calculo_rangos_edad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicamento',
            name='unidad_dosis_kg',
            field=models.CharField(
                blank=True,
                choices=[
                    ('mL',         'mL/kg'),
                    ('gotas',      'gotas/kg'),
                    ('tableta',    'tabletas/kg'),
                    ('sobre',      'sobres/kg'),
                    ('puff',       'puffs/kg'),
                    ('aplicacion', 'aplicaciones/kg'),
                    ('mg',         'mg/kg'),
                    ('mcg',        'mcg/kg'),
                    ('UI',         'UI/kg'),
                ],
                default='mg',
                max_length=10,
                verbose_name='Unidad de dosis/kg',
            ),
        ),
    ]
