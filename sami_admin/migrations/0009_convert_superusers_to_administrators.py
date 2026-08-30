from django.conf import settings
from django.db import migrations


def convert_superusers_to_administrators(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Group = apps.get_model("auth", "Group")
    administrator_group, _ = Group.objects.get_or_create(name="Administrador")

    for user in User.objects.filter(is_superuser=True):
        user.is_superuser = False
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
        user.groups.add(administrator_group)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sami_admin", "0008_cotizacion_edades_ninos_cotizaciondestino"),
    ]

    operations = [
        migrations.RunPython(
            convert_superusers_to_administrators,
            migrations.RunPython.noop,
        ),
    ]
