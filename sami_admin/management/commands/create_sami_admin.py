from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crea la primera cuenta Administrador de SAMI sin usar superusuarios."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Nombre de usuario para iniciar sesión.")
        parser.add_argument("--email", default="", help="Correo electrónico.")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"].strip()
        if not username:
            raise CommandError("El nombre de usuario no puede estar vacío.")
        if User.objects.filter(username=username).exists():
            raise CommandError(f"Ya existe el usuario {username}.")

        password = getpass("Contraseña: ")
        confirmation = getpass("Confirmar contraseña: ")
        if password != confirmation:
            raise CommandError("Las contraseñas no coinciden.")

        user = User(username=username, email=options["email"].strip())
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc

        with transaction.atomic():
            user.is_active = True
            user.is_staff = True
            user.is_superuser = False
            user.set_password(password)
            user.save()
            administrator_group, _ = Group.objects.get_or_create(
                name="Administrador"
            )
            user.groups.add(administrator_group)

        self.stdout.write(
            self.style.SUCCESS(f"Administrador {username} creado correctamente.")
        )
