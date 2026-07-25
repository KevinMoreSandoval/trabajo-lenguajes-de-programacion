from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    rol = models.ForeignKey(
        Rol,
        on_delete=models.RESTRICT,
        db_column="rol_id",
        null=True,
        blank=True,
        related_name="usuarios",
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    dni = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(r"^\d{8}$", "El DNI debe tener exactamente 8 dígitos.")
        ],
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                r"^\d{9}$", "El número de teléfono debe tener exactamente 9 dígitos."
            )
        ],
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=150, unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-fecha_creacion", "username"]

    def __str__(self):
        return self.get_full_name() or self.email or self.username or str(self.pk)


class Cliente(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        db_column="usuario_id",
        primary_key=True,
        related_name="cliente",
    )

    class Meta:
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"Cliente: {self.usuario.get_full_name() or self.usuario.email}"


class Admin(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        db_column="usuario_id",
        primary_key=True,
        related_name="admin",
    )

    class Meta:
        db_table = "admins"
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

    def __str__(self):
        return f"Admin: {self.usuario.get_full_name() or self.usuario.email}"


class Recepcionista(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        db_column="usuario_id",
        primary_key=True,
        related_name="recepcionista",
    )

    class Meta:
        db_table = "recepcionistas"
        verbose_name = "Recepcionista"
        verbose_name_plural = "Recepcionistas"

    def __str__(self):
        return f"Recepcionista: {self.usuario.get_full_name() or self.usuario.email}"
