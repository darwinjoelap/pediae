from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0012_consulta_indicaciones_alter_consulta_tratamiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultaservicio',
            name='costo_adquisicion_usd',
            field=models.DecimalField(
                blank=True, null=True, default=None,
                max_digits=8, decimal_places=2,
                verbose_name='Costo adquisición USD al momento',
            ),
        ),
    ]
