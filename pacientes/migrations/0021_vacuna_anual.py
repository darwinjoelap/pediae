from django.db import migrations, models


def marcar_vacunas_anuales(apps, schema_editor):
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    # Influenza es la principal vacuna anual del PAI Venezuela
    Vacuna.objects.filter(
        nombre__icontains='influenza',
        tenant=None,
    ).update(es_anual=True)


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0020_pcv13_refuerzo_18meses'),
    ]

    operations = [
        # 1. Añadir campo es_anual a Vacuna
        migrations.AddField(
            model_name='vacuna',
            name='es_anual',
            field=models.BooleanField(
                default=False,
                verbose_name='Vacuna anual',
                help_text='Permite registrar múltiples aplicaciones año a año (ej: Influenza).',
            ),
        ),
        # 2. Eliminar la restricción unique_together de VacunaAplicada
        migrations.AlterUniqueTogether(
            name='vacunaaplicada',
            unique_together=set(),
        ),
        # 3. Marcar Influenza como anual en datos existentes
        migrations.RunPython(marcar_vacunas_anuales, migrations.RunPython.noop),
    ]
