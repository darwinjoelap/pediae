from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0006_paciente_campos_pediatricos'),
    ]

    operations = [
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
    ]
