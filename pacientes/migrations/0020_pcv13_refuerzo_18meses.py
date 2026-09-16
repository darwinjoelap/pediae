"""
Migración 0020: Mueve el refuerzo de Neumococo PCV13 (dosis 4) de 12 meses a 18 meses.

- Solo actualiza el catálogo (modelo Vacuna, tenant=None).
- Los registros VacunaAplicada de pacientes NO se modifican:
  cada paciente conserva su fecha real de aplicación.
"""
from django.db import migrations


def mover_pcv13_a_18m(apps, schema_editor):
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    Vacuna.objects.filter(
        nombre='Neumococo PCV13',
        dosis_numero=4,
        tenant=None,
    ).update(
        edad_recomendada_meses=18,
        edad_max_meses=24,
        grupo_etario='18 meses',
    )


def revertir_pcv13_a_12m(apps, schema_editor):
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    Vacuna.objects.filter(
        nombre='Neumococo PCV13',
        dosis_numero=4,
        tenant=None,
    ).update(
        edad_recomendada_meses=12,
        edad_max_meses=15,
        grupo_etario='12 meses',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0019_remove_pesquisarealizada_unique_paciente_pesquisa_and_more'),
    ]

    operations = [
        migrations.RunPython(mover_pcv13_a_18m, revertir_pcv13_a_12m),
    ]
