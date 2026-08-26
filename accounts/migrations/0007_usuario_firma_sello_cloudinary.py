from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_usuario_firma_sello'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuario',
            name='firma',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='sello',
        ),
        migrations.AddField(
            model_name='usuario',
            name='firma_public_id',
            field=models.CharField(
                blank=True, max_length=500,
                verbose_name='Firma digital (Cloudinary public_id)',
                help_text='PNG con fondo transparente recomendado. Aparece encima de la línea de firma en los PDFs.',
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='sello_public_id',
            field=models.CharField(
                blank=True, max_length=500,
                verbose_name='Sello / Timbre (Cloudinary public_id)',
                help_text='PNG con fondo transparente recomendado. Aparece al lado de la firma en los PDFs.',
            ),
        ),
    ]
