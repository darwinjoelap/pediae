from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0007_paciente_filiacion_representante'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='paciente',
            unique_together=set(),
        ),
    ]
