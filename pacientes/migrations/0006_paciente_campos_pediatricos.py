from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0005_paciente_ciclo_caracteristicas'),
    ]

    operations = [
        migrations.AddField(
            model_name='paciente',
            name='no_cedulado',
            field=models.BooleanField(
                default=False,
                help_text='Marcar si el paciente aún no tiene cédula (niño/a sin cédula)',
                verbose_name='Paciente no cedulado',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nombre_padre',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nombre del padre'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nombre_madre',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nombre de la madre'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nombre_representante',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nombre del representante'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='filiacion_representante',
            field=models.CharField(
                blank=True,
                choices=[('madre', 'Madre'), ('padre', 'Padre'), ('otro', 'Otro')],
                max_length=10,
                verbose_name='Filiación del representante',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='parentesco_representante',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Parentesco (si es otro)',
                help_text='Ej: abuela, tío, tutor legal',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='cedula_representante',
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[django.core.validators.RegexValidator(
                    regex=r'^[VvEe]-\d{6,9}-\d+$',
                    message='La cédula del representante debe tener formato V-xxxxxxxx-N (ej: V-12345678-1)',
                )],
                verbose_name='Cédula del representante',
                help_text='Formato: V-12345678-1 (el número final identifica al hijo/representado)',
            ),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='cedula',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Formato: V-12345678 o E-12345678',
                max_length=15,
                validators=[django.core.validators.RegexValidator(
                    regex=r'^[VvEe]-\d{6,9}$',
                    message='La cédula debe tener formato V-xxxxxxxx o E-xxxxxxxx',
                )],
                verbose_name='Cédula del paciente',
            ),
        ),
    ]
