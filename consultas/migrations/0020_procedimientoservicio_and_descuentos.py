# Generado a mano — parte 1/3 de la migración a servicios múltiples en
# Procedimiento + exoneración/descuento por línea de servicio.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('consultas', '0019_alter_medicamento_concentracion_mg_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultaservicio',
            name='exonerado',
            field=models.BooleanField(default=False, verbose_name='Exonerado'),
        ),
        migrations.AddField(
            model_name='consultaservicio',
            name='descuento_usd',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='Descuento (USD)'),
        ),
        migrations.CreateModel(
            name='ProcedimientoServicio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('precio_usd', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Precio USD al momento')),
                ('costo_adquisicion_usd', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True, verbose_name='Costo adquisición USD al momento')),
                ('tasa_cambio', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Tasa al momento')),
                ('exonerado', models.BooleanField(default=False, verbose_name='Exonerado')),
                ('descuento_usd', models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='Descuento (USD)')),
                ('procedimiento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servicios_usados', to='consultas.procedimiento')),
                ('servicio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='procedimientos_usados', to='servicios.servicio')),
            ],
            options={
                'verbose_name': 'Servicio de procedimiento',
                'verbose_name_plural': 'Servicios de procedimiento',
            },
        ),
    ]
