from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_usuario_telefono'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='firma',
            field=models.ImageField(
                blank=True, null=True,
                upload_to='firmas/',
                verbose_name='Firma digital',
                help_text='PNG con fondo transparente recomendado. Aparece encima de la línea de firma en los PDFs.',
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='sello',
            field=models.ImageField(
                blank=True, null=True,
                upload_to='sellos/',
                verbose_name='Sello / Timbre',
                help_text='PNG con fondo transparente recomendado. Aparece al lado de la firma en los PDFs.',
            ),
        ),
    ]
