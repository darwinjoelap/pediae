from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0010_paciente_limpiar_campos_ginecologicos'),
        ('tenant', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Vacuna',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Vacuna')),
                ('enfermedad', models.CharField(blank=True, max_length=200, verbose_name='Protege contra')),
                ('dosis_numero', models.PositiveSmallIntegerField(verbose_name='N° dosis')),
                ('edad_recomendada_meses', models.PositiveSmallIntegerField(
                    help_text='0 = al nacer, 2 = 2 meses, 12 = 1 año, etc.',
                    verbose_name='Edad recomendada (meses)',
                )),
                ('edad_max_meses', models.PositiveSmallIntegerField(
                    blank=True, null=True,
                    help_text='Si se supera esta edad se marca como atrasada.',
                    verbose_name='Edad máxima (meses)',
                )),
                ('es_pai', models.BooleanField(default=True, verbose_name='Vacuna PAI (esquema oficial)')),
                ('activa', models.BooleanField(default=True)),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='Orden de visualización')),
                ('tenant', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vacunas_extra',
                    to='tenant.tenant',
                    verbose_name='Consultorio',
                    help_text='Null = vacuna PAI (compartida). Con tenant = vacuna adicional del consultorio.',
                )),
            ],
            options={
                'verbose_name': 'Vacuna',
                'verbose_name_plural': 'Vacunas',
                'ordering': ['orden', 'edad_recomendada_meses', 'dosis_numero'],
            },
        ),
        migrations.CreateModel(
            name='VacunaAplicada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(verbose_name='Fecha de aplicación')),
                ('lote', models.CharField(blank=True, max_length=50, verbose_name='Lote / Laboratorio')),
                ('observaciones', models.CharField(blank=True, max_length=300, verbose_name='Observaciones')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('paciente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vacunas_aplicadas',
                    to='pacientes.paciente',
                )),
                ('vacuna', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='aplicaciones',
                    to='pacientes.vacuna',
                )),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vacunas_aplicadas',
                    to='tenant.tenant',
                )),
                ('aplicada_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='vacunas_aplicadas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Vacuna aplicada',
                'verbose_name_plural': 'Vacunas aplicadas',
                'ordering': ['fecha'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='vacunaaplicada',
            unique_together={('paciente', 'vacuna')},
        ),
    ]
