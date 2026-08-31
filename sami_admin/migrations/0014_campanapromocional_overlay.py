from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sami_admin", "0013_lugarturistico_actividades_destacadas_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="campanapromocional",
            name="color_superposicion",
            field=models.CharField(
                "color de superposición",
                default="#06152B",
                help_text="Color aplicado sobre la imagen para mejorar el contraste.",
                max_length=7,
                validators=[
                    RegexValidator(
                        message="Selecciona un color hexadecimal válido.",
                        regex="^#[0-9A-Fa-f]{6}$",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="campanapromocional",
            name="opacidad_superposicion",
            field=models.PositiveSmallIntegerField(
                "transparencia del color",
                default=55,
                help_text="0 muestra la imagen original y 100 cubre completamente la imagen.",
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
    ]
