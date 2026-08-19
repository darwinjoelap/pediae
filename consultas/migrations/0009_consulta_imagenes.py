# Generated manually on 2026-08-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0008_procedimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='consulta',
            name='imagenes',
            field=models.TextField(
                blank=True,
                help_text='Mamografía, ecografía, densitometría ósea, etc.',
                verbose_name='Imágenes',
            ),
        ),
    ]
