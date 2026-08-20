from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0008_remove_unique_cedula'),
    ]

    operations = [
        migrations.AddField(
            model_name='paciente',
            name='sexo',
            field=models.CharField(
                blank=True,
                choices=[('M', 'Masculino'), ('F', 'Femenino')],
                max_length=1,
                verbose_name='Sexo biológico',
            ),
        ),
    ]
