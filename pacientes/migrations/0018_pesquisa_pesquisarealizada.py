"""
Migración 0018: Crea los modelos Pesquisa y PesquisaRealizada,
y carga el catálogo inicial de 4 pesquisas estándar.
"""
from django.db import migrations, models
import django.db.models.deletion


PESQUISAS_INICIALES = [
    ('Eco de cadera',         'Ecografía de caderas (displasia del desarrollo)', 10),
    ('Eco renal / abdominal', 'Ecografía renal y abdominal',                     20),
    ('Oftalmológica',         'Evaluación oftalmológica pediátrica',              30),
    ('Audiología',            'Evaluación audiológica / otoemisiones acústicas',  40),
]


def cargar_pesquisas(apps, schema_editor):
    Pesquisa = apps.get_model('pacientes', 'Pesquisa')
    for nombre, descripcion, orden in PESQUISAS_INICIALES:
        Pesquisa.objects.get_or_create(
            nombre=nombre,
            tenant=None,
            defaults=dict(descripcion=descripcion, orden=orden, activa=True),
        )


def borrar_pesquisas(apps, schema_editor):
    Pesquisa = apps.get_model('pacientes', 'Pesquisa')
    Pesquisa.objects.filter(tenant=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0017_nuevo_esquema_vacunas'),
        ('accounts', '0001_initial'),
        ('tenant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pesquisa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Pesquisa')),
                ('descripcion', models.CharField(blank=True, max_length=200, verbose_name='Descripción')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('activa', models.BooleanField(default=True)),
                ('tenant', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pesquisas_extra',
                    to='tenant.tenant',
                    verbose_name='Consultorio',
                )),
            ],
            options={
                'verbose_name': 'Pesquisa',
                'verbose_name_plural': 'Pesquisas',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='PesquisaRealizada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(blank=True, null=True, verbose_name='Fecha de realización')),
                ('comentario', models.CharField(blank=True, max_length=300, verbose_name='Comentario / Resultado')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('paciente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pesquisas_realizadas',
                    to='pacientes.paciente',
                )),
                ('pesquisa', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='realizaciones',
                    to='pacientes.pesquisa',
                )),
                ('realizada_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pesquisas_realizadas',
                    to='accounts.usuario',
                )),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pesquisas_realizadas',
                    to='tenant.tenant',
                )),
            ],
            options={
                'verbose_name': 'Pesquisa realizada',
                'verbose_name_plural': 'Pesquisas realizadas',
                'ordering': ['pesquisa__orden'],
            },
        ),
        migrations.AddConstraint(
            model_name='pesquisarealizada',
            constraint=models.UniqueConstraint(
                fields=['paciente', 'pesquisa'],
                name='unique_paciente_pesquisa',
            ),
        ),
        migrations.RunPython(cargar_pesquisas, borrar_pesquisas),
    ]
