import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Cotizacion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cliente_nombre", models.CharField(max_length=180)),
                ("cliente_correo", models.EmailField(max_length=254)),
                ("destino", models.CharField(max_length=180)),
                (
                    "precio_estimado",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "fecha_creacion",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("aprobada", "Aprobada"),
                            ("rechazada", "Rechazada"),
                        ],
                        db_index=True,
                        default="pendiente",
                        max_length=12,
                    ),
                ),
                (
                    "asesor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cotizaciones",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "cotización",
                "verbose_name_plural": "cotizaciones",
                "ordering": ("-fecha_creacion",),
            },
        ),
    ]
