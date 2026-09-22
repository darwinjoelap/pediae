# Generado a mano — parte 3/3. Quita del encabezado Procedimiento los
# campos que ahora viven en ProcedimientoServicio (ya migrados en el
# paso anterior).
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0021_migrar_procedimientos_a_servicios'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='procedimiento',
            name='servicio',
        ),
        migrations.RemoveField(
            model_name='procedimiento',
            name='precio_usd',
        ),
        migrations.RemoveField(
            model_name='procedimiento',
            name='tasa_cambio',
        ),
    ]
