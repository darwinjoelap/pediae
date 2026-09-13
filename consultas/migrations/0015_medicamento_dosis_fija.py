from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0014_add_medicamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicamento',
            name='dosis_fija',
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name='Dosis fija',
                help_text=(
                    'Para medicamentos donde la dosis NO depende del peso. '
                    'Ej: 2 puffs, 1 inhalación, 3 gotas. '
                    'Si se completa, ignora los campos mg/kg y se usa directamente como {{DOSIS}}.'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='medicamento',
            name='unidad_resultado',
            field=models.CharField(
                blank=True,
                max_length=10,
                verbose_name='Unidad del resultado',
                choices=[
                    ('mL',         'mL (jarabe / gotas)'),
                    ('tableta',    'Tableta / cápsula'),
                    ('mg',         'mg directo'),
                    ('UI',         'Unidades internacionales'),
                    ('gotas',      'Gotas'),
                    ('puff',       'Puff / inhalación'),
                    ('aplicacion', 'Aplicación'),
                    ('sobre',      'Sobre'),
                ],
            ),
        ),
    ]
