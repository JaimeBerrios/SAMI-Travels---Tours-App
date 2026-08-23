import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial administrator when explicitly enabled."

    def handle(self, *args, **options):
        enabled = os.environ.get("DJANGO_BOOTSTRAP_ADMIN", "false").lower()
        if enabled not in {"1", "true", "yes", "on"}:
            return

        username = os.environ.get("DJANGO_ADMIN_USERNAME", "").strip()
        email = os.environ.get("DJANGO_ADMIN_EMAIL", "").strip()
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")

        if not username or not email or not password:
            raise CommandError(
                "DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_EMAIL and "
                "DJANGO_ADMIN_PASSWORD are required when admin bootstrap is enabled."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        changed_fields = []
        if not user.is_staff:
            user.is_staff = True
            changed_fields.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            changed_fields.append("is_superuser")

        if created:
            user.set_password(password)
            changed_fields.append("password")

        if changed_fields:
            user.save(update_fields=changed_fields)

        action = "created" if created else "already exists"
        self.stdout.write(self.style.SUCCESS(f'Administrator "{username}" {action}.'))
