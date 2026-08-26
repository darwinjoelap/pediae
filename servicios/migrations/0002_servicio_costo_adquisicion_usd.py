from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicio',
            name='costo_adquisicion_usd',
            field=models.DecimalField(
                blank=True, null=True, default=None,
                max_digits=8, decimal_places=2,
                verbose_name='Costo de adquisición (USD)',
                help_text='Ej: vacunas. Opcional. Se usa para calcular el ingreso real.',
            ),
        ),
    ]
