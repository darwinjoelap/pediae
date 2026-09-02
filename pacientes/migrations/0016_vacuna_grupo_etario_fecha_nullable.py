"""
Migración 0016: Esquema de vacunación — mejoras de modelo
  - Agrega campo grupo_etario a Vacuna
  - Hace nullable el campo fecha en VacunaAplicada (permite marcar rápido sin fecha)
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0015_historia_clinica_estructurada'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacuna',
            name='grupo_etario',
            field=models.CharField(
                blank=True,
                default='',
                max_length=60,
                verbose_name='Grupo etario',
                help_text='Ej: Recién nacido (0-28 días), 2 meses, 12 meses, Adolescentes',
            ),
        ),
        migrations.AlterField(
            model_name='vacunaaplicada',
            name='fecha',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Fecha de aplicación',
            ),
        ),
    ]
