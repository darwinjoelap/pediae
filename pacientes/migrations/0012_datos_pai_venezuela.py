"""
Migración de datos: Esquema PAI Venezuela
Carga el catálogo de vacunas del Programa Ampliado de Inmunización de Venezuela.
tenant=None → compartido por todos los consultorios.
"""
from django.db import migrations


PAI_VACUNAS = [
    # (nombre, enfermedad, dosis_numero, edad_meses, edad_max_meses, orden)
    # ── Al nacer ────────────────────────────────────────────────────────────
    ('BCG', 'Tuberculosis', 1, 0, 2, 10),
    ('HepB', 'Hepatitis B', 1, 0, 1, 20),
    # ── 2 meses ─────────────────────────────────────────────────────────────
    ('Pentavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB', 1, 2, 4, 30),
    ('Rotavirus', 'Gastroenteritis por rotavirus', 1, 2, 4, 40),
    ('Neumococo 13v', 'Enfermedad neumocócica', 1, 2, 4, 50),
    ('Polio OPV', 'Poliomielitis', 1, 2, 4, 60),
    # ── 4 meses ─────────────────────────────────────────────────────────────
    ('Pentavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB', 2, 4, 6, 30),
    ('Rotavirus', 'Gastroenteritis por rotavirus', 2, 4, 7, 40),
    ('Neumococo 13v', 'Enfermedad neumocócica', 2, 4, 6, 50),
    ('Polio OPV', 'Poliomielitis', 2, 4, 6, 60),
    # ── 6 meses ─────────────────────────────────────────────────────────────
    ('Pentavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB', 3, 6, 9, 30),
    ('HepB', 'Hepatitis B', 3, 6, 9, 20),
    ('Polio OPV', 'Poliomielitis', 3, 6, 9, 60),
    ('Influenza', 'Influenza estacional', 1, 6, 8, 70),
    # ── 7 meses ─────────────────────────────────────────────────────────────
    ('Influenza', 'Influenza estacional', 2, 7, 9, 70),
    # ── 12 meses ────────────────────────────────────────────────────────────
    ('SRP', 'Sarampión, Rubéola, Parotiditis', 1, 12, 15, 80),
    ('Varicela', 'Varicela', 1, 12, 15, 90),
    ('Neumococo 13v', 'Enfermedad neumocócica', 3, 12, 15, 50),
    ('Hepatitis A', 'Hepatitis A', 1, 12, 18, 100),
    # ── 15 meses ────────────────────────────────────────────────────────────
    ('Polio OPV', 'Poliomielitis', 4, 15, 18, 60),
    # ── 18 meses ────────────────────────────────────────────────────────────
    ('Pentavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB', 4, 18, 24, 30),
    ('Hepatitis A', 'Hepatitis A', 2, 18, 24, 100),
    # ── 4 años ──────────────────────────────────────────────────────────────
    ('DPT', 'Difteria, Tétanos, Tos ferina', 5, 48, 60, 110),
    ('SRP', 'Sarampión, Rubéola, Parotiditis', 2, 48, 60, 80),
    ('Polio OPV', 'Poliomielitis', 5, 48, 60, 60),
    ('Varicela', 'Varicela', 2, 48, 60, 90),
    # ── Influenza anual (se registra como nueva dosis cada año) ────────────
    ('Influenza (anual)', 'Influenza estacional (refuerzo anual)', 1, 12, None, 75),
]


def cargar_pai(apps, schema_editor):
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    for nombre, enfermedad, dosis, edad, edad_max, orden in PAI_VACUNAS:
        Vacuna.objects.get_or_create(
            nombre=nombre,
            dosis_numero=dosis,
            edad_recomendada_meses=edad,
            tenant=None,
            defaults=dict(
                enfermedad=enfermedad,
                edad_max_meses=edad_max,
                es_pai=True,
                activa=True,
                orden=orden,
            ),
        )


def descargar_pai(apps, schema_editor):
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    Vacuna.objects.filter(tenant=None, es_pai=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0011_vacuna_vacunaaplicada'),
    ]

    operations = [
        migrations.RunPython(cargar_pai, descargar_pai),
    ]
