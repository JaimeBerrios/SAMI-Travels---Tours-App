from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_alter_solicitudcontacto_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitudcontacto",
            name="equipaje_estimado",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="solicitudcontacto",
            name="hora_salida_preferida",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="solicitudcontacto",
            name="motivo_vuelo_privado",
            field=models.CharField(
                blank=True,
                choices=[
                    ("negocios", "Negocios"),
                    ("turismo", "Turismo"),
                    ("grupo", "Viaje grupal"),
                    ("emergencia", "Necesidad urgente"),
                    ("otro", "Otro"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="solicitudcontacto",
            name="preferencia_aeronave",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name="solicitudcontacto",
            name="servicio",
            field=models.CharField(
                choices=[
                    ("vuelo", "Cotización de vuelo"),
                    ("vuelo privado", "Cotización de vuelo privado"),
                    ("tour", "Cotización de tour"),
                    ("vuelo y tour", "Vuelo y tour"),
                ],
                max_length=20,
            ),
        ),
    ]
