# Generado a mano — parte 2/3. Traslada cada Procedimiento existente
# (servicio único) a una fila ProcedimientoServicio, antes de borrar los
# campos viejos en la siguiente migración. No debe perderse historial de
# producción (Dra. Anaís Báez / Dra. Hernández Escalona).
from django.db import migrations


def migrar_datos(apps, schema_editor):
    Procedimiento = apps.get_model('consultas', 'Procedimiento')
    ProcedimientoServicio = apps.get_model('consultas', 'ProcedimientoServicio')

    for proc in Procedimiento.objects.all():
        if proc.servicio_id is None:
            continue
        costo_adquisicion_usd = None
        try:
            costo_adquisicion_usd = proc.servicio.costo_adquisicion_usd
        except Exception:
            pass
        ProcedimientoServicio.objects.create(
            procedimiento=proc,
            servicio_id=proc.servicio_id,
            precio_usd=proc.precio_usd,
            costo_adquisicion_usd=costo_adquisicion_usd,
            tasa_cambio=proc.tasa_cambio,
        )


def revertir_datos(apps, schema_editor):
    # No se puede reconstruir un solo servicio/precio a partir de varias
    # líneas de forma confiable; se deja vacío a propósito.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0020_procedimientoservicio_and_descuentos'),
    ]

    operations = [
        migrations.RunPython(migrar_datos, revertir_datos),
    ]
