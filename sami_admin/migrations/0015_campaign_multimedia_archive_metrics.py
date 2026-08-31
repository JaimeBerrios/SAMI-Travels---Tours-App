from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sami_admin", "0014_campanapromocional_overlay"),
    ]

    operations = [
        migrations.AddField(
            model_name="campanapromocional",
            name="archivada_en",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="clics",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="conversiones",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="impresiones",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="multimedia_escritorio",
            field=models.FileField(blank=True, upload_to="campanas/multimedia/escritorio/"),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="multimedia_movil",
            field=models.FileField(blank=True, upload_to="campanas/multimedia/movil/"),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="orden",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Entre campañas con la misma prioridad, el número menor aparece primero.",
            ),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="tipo_multimedia",
            field=models.CharField(
                choices=[("imagen", "Imagen"), ("gif", "GIF animado"), ("video", "Video")],
                default="imagen",
                help_text="Las imágenes siempre se conservan como portada y respaldo.",
                max_length=10,
            ),
        ),
        migrations.AlterModelOptions(
            name="campanapromocional",
            options={
                "ordering": ("-prioridad", "orden", "-fecha_inicio", "-id"),
                "verbose_name": "campaña promocional",
                "verbose_name_plural": "campañas promocionales",
            },
        ),
    ]
