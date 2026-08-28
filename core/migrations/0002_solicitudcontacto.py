from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="SolicitudContacto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("nombre", models.CharField(max_length=180)),
                ("contacto", models.CharField(max_length=180)),
                ("servicio", models.CharField(choices=[("vuelo", "Cotización de vuelo"), ("tour", "Cotización de tour"), ("vuelo y tour", "Vuelo y tour")], max_length=20)),
                ("destino", models.CharField(blank=True, max_length=180)),
                ("detalles", models.TextField(blank=True)),
                ("atendida", models.BooleanField(db_index=True, default=False)),
            ],
            options={
                "verbose_name": "solicitud de contacto",
                "verbose_name_plural": "solicitudes de contacto",
                "ordering": ("atendida", "-creado_en"),
            },
        ),
    ]
