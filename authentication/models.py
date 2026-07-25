from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class Rol(models.Model):
    ADMIN = 'Admin'
    RECEPCIONISTA = 'Recepcionista'
    CLIENTE = 'Cliente'
    ROLES_VALIDOS = (ADMIN, RECEPCIONISTA, CLIENTE)

    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.nombre not in self.ROLES_VALIDOS:
            raise ValidationError({'nombre': 'Solo se permiten los roles Admin, Recepcionista y Cliente.'})

class Usuario(AbstractUser):
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column='rol_id', null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    dni = models.CharField(
        max_length=15, 
        unique=True, 
        null=True, 
        blank=True,
        validators=[RegexValidator(r'^\d{8}$', 'El DNI debe tener exactamente 8 dígitos.')]
    )
    telefono = models.CharField(
        max_length=20,
        null=True, blank=True,
        validators=[RegexValidator(r'^\d{9}$', 'El número de teléfono debe tener exactamente 9 dígitos.')]
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Campos que Django requiere internamente para AbstractUser
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=150, unique=True)

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'usuarios'

    @property
    def rol_nombre(self):
        return self.rol.nombre if self.rol else Rol.CLIENTE

    @property
    def es_admin(self):
        return self.rol_nombre == Rol.ADMIN

    @property
    def es_recepcionista(self):
        return self.rol_nombre == Rol.RECEPCIONISTA

    @property
    def es_cliente(self):
        return self.rol_nombre == Rol.CLIENTE

    @property
    def es_operador(self):
        return self.es_admin or self.es_recepcionista

    def save(self, *args, **kwargs):
        if self.is_superuser:
            admin_rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMIN)
            self.rol = admin_rol
            self.is_staff = True
            self.activo = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.username or f'Usuario {self.pk}'
