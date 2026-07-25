"""
Migración de datos: Crea los roles Admin y Recepcionista,
y siembra un usuario administrador y un recepcionista con sus perfiles.
"""

from django.db import migrations
from django.contrib.auth.hashers import make_password


def seed_admin_recepcionista(apps, schema_editor):
    Rol = apps.get_model("authentication", "Rol")
    Usuario = apps.get_model("authentication", "Usuario")
    Admin = apps.get_model("authentication", "Admin")
    Recepcionista = apps.get_model("authentication", "Recepcionista")

    # Crear roles si no existen
    rol_admin, _ = Rol.objects.get_or_create(nombre="Admin")
    Rol.objects.get_or_create(nombre="Cliente")
    rol_recepcionista, _ = Rol.objects.get_or_create(nombre="Recepcionista")

    # ---------- Admin ----------
    if not Usuario.objects.filter(email="admin@canchas.com").exists():
        admin_user = Usuario.objects.create(
            email="admin@canchas.com",
            username="admin_canchas",
            password=make_password("AdminSecure123!"),
            first_name="Carlos",
            last_name="Administrador",
            dni="12345678",
            telefono="987654321",
            rol=rol_admin,
            activo=True,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        Admin.objects.get_or_create(usuario=admin_user)

    # ---------- Recepcionista ----------
    if not Usuario.objects.filter(email="recepcionista@canchas.com").exists():
        recep_user = Usuario.objects.create(
            email="recepcionista@canchas.com",
            username="recepcionista_canchas",
            password=make_password("RecepcionSecure123!"),
            first_name="María",
            last_name="Gómez López",
            dni="11223344",
            telefono="945678901",
            rol=rol_recepcionista,
            activo=True,
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )
        Recepcionista.objects.get_or_create(usuario=recep_user)


def reverse_seed(apps, schema_editor):
    """Deshace la migración eliminando los usuarios sembrados."""
    Usuario = apps.get_model("authentication", "Usuario")
    Usuario.objects.filter(
        email__in=["admin@canchas.com", "recepcionista@canchas.com"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0009_admin_cliente_recepcionista"),
    ]

    operations = [
        migrations.RunPython(seed_admin_recepcionista, reverse_seed),
    ]
