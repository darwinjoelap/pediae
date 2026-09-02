"""
Migración 0017: Reemplaza catálogo PAI Venezuela por el nuevo esquema internacional
agrupado por etapa de vida (Recién nacido → Adolescentes → Anual).

ADVERTENCIA: Elimina las VacunaAplicada referenciadas a vacunas PAI antiguas
antes de borrar el catálogo.  Ejecutar sólo en entornos donde se acepte
la pérdida de registros históricos bajo la nomenclatura anterior.
"""
from django.db import migrations

# ── Nuevo catálogo ─────────────────────────────────────────────────────────────
# (nombre, enfermedad, dosis_numero, edad_meses, edad_max_meses, orden, grupo_etario)

NEW_VACUNAS = [
    # ── Recién nacido (0-28 días) ──────────────────────────────────────────────
    ('BCG',         'Tuberculosis',  1, 0, 2,  10, 'Recién nacido (0-28 días)'),
    ('Hepatitis B', 'Hepatitis B',   1, 0, 1,  20, 'Recién nacido (0-28 días)'),

    # ── 2 meses ────────────────────────────────────────────────────────────────
    ('Pentavalente / Hexavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB',  1, 2, 4, 30, '2 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis',                              1, 2, 4, 40, '2 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica',                     1, 2, 4, 50, '2 meses'),
    ('Rotavirus',                  'Gastroenteritis por rotavirus',               1, 2, 3, 60, '2 meses'),

    # ── 4 meses ────────────────────────────────────────────────────────────────
    ('Pentavalente / Hexavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB',  2, 4, 6, 30, '4 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis',                              2, 4, 6, 40, '4 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica',                     2, 4, 6, 50, '4 meses'),
    ('Rotavirus',                  'Gastroenteritis por rotavirus',               2, 4, 6, 60, '4 meses'),

    # ── 6 meses ────────────────────────────────────────────────────────────────
    ('Pentavalente / Hexavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB',  3, 6, 9, 30, '6 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis',                              3, 6, 9, 40, '6 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica',                     3, 6, 9, 50, '6 meses'),
    ('Rotavirus',                  'Gastroenteritis por rotavirus',               3, 6, 8, 60, '6 meses'),
    ('Influenza',                  'Influenza estacional',                        1, 6, 8, 70, '6 meses'),

    # ── 7 meses ────────────────────────────────────────────────────────────────
    ('Influenza',                  'Influenza estacional',                        2, 7, 9, 70, '7 meses'),

    # ── 9 meses ────────────────────────────────────────────────────────────────
    ('Meningococo conjugada',      'Enfermedad meningocócica',                   1, 9, 12, 80, '9 meses'),

    # ── 12 meses ───────────────────────────────────────────────────────────────
    ('Triple Viral (SRP)',         'Sarampión, Rubéola, Parotiditis',             1, 12, 15,   90, '12 meses'),
    ('Fiebre Amarilla',            'Fiebre Amarilla',                             1, 12, None, 100, '12 meses'),
    ('Hepatitis A',                'Hepatitis A',                                 1, 12, 18,  110, '12 meses'),
    ('Varicela',                   'Varicela',                                    1, 12, 15,  120, '12 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica (refuerzo)',            4, 12, 15,   50, '12 meses'),
    ('Meningococo conjugada',      'Enfermedad meningocócica',                    2, 12, 15,   80, '12 meses'),

    # ── 18 meses ───────────────────────────────────────────────────────────────
    ('Pentavalente / DPT',         'Difteria, Tétanos, Tos ferina, Hib (1.er refuerzo)', 4, 18, 24, 30, '18 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis (1.er refuerzo)',               4, 18, 24,  40, '18 meses'),
    ('Triple Viral (SRP)',         'Sarampión, Rubéola, Parotiditis',             2, 18, 24,  90, '18 meses'),
    ('Hepatitis A',                'Hepatitis A (6 m después de la 1.ª dosis)',   2, 18, 30, 110, '18 meses'),

    # ── 4 a 6 años ─────────────────────────────────────────────────────────────
    ('DPT',                        'Difteria, Tétanos, Tos ferina (2.º refuerzo)', 5, 48, 72, 130, '4 a 6 años'),
    ('Polio (VPI / bVPO)',         'Poliomielitis (2.º refuerzo)',                5, 48, 72,  40, '4 a 6 años'),
    ('Triple Viral (SRP)',         'Sarampión, Rubéola, Parotiditis (refuerzo)',  3, 48, 72,  90, '4 a 6 años'),
    ('Varicela',                   'Varicela',                                    2, 48, 72, 120, '4 a 6 años'),

    # ── Adolescentes (9-18 años) ────────────────────────────────────────────────
    ('VPH',              'Virus del Papiloma Humano (esquema 2 dosis: 9-14 a.)',  1, 108, 216, 140, 'Adolescentes (9-18 años)'),
    ('Tdap',             'Difteria, Tétanos, Tos ferina acelular (refuerzo)',     1, 132, 216, 150, 'Adolescentes (9-18 años)'),
    ('Meningococo MCV4', 'Enfermedad meningocócica (MenACWY)',                    1, 132, 216, 160, 'Adolescentes (9-18 años)'),

    # ── Vacunación anual ────────────────────────────────────────────────────────
    ('Influenza (anual)', 'Influenza estacional (dosis anual desde los 6 m)',     1, 6, None,  75, 'Vacunación anual'),
]


def reemplazar_esquema(apps, schema_editor):
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    VacunaAplicada = apps.get_model('pacientes', 'VacunaAplicada')

    # 1. Obtener IDs PAI actuales
    old_ids = list(
        Vacuna.objects.filter(tenant=None, es_pai=True).values_list('pk', flat=True)
    )

    # 2. Eliminar aplicaciones que referencien esas vacunas (PROTECT impide el delete directo)
    if old_ids:
        VacunaAplicada.objects.filter(vacuna_id__in=old_ids).delete()
        Vacuna.objects.filter(pk__in=old_ids).delete()

    # 3. Cargar nuevo catálogo
    for nombre, enfermedad, dosis, edad, edad_max, orden, grupo in NEW_VACUNAS:
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
                grupo_etario=grupo,
            ),
        )


def revertir_esquema(apps, schema_editor):
    """Elimina el nuevo catálogo (sin restaurar el anterior)."""
    Vacuna = apps.get_model('pacientes', 'Vacuna')
    VacunaAplicada = apps.get_model('pacientes', 'VacunaAplicada')
    ids = list(Vacuna.objects.filter(tenant=None, es_pai=True).values_list('pk', flat=True))
    if ids:
        VacunaAplicada.objects.filter(vacuna_id__in=ids).delete()
        Vacuna.objects.filter(pk__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0016_vacuna_grupo_etario_fecha_nullable'),
    ]

    operations = [
        migrations.RunPython(reemplazar_esquema, revertir_esquema),
    ]
