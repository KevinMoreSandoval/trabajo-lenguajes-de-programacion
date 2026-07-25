from django.contrib import admin
from .models import Rol, Usuario, Cliente, Admin, Recepcionista


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("email", "get_full_name", "rol", "activo", "fecha_creacion")
    list_filter = ("activo", "rol", "fecha_creacion")
    search_fields = ("email", "username", "first_name", "last_name", "dni")
    ordering = ("-fecha_creacion",)
    fieldsets = (
        (
            "Información Personal",
            {
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "dni",
                    "fecha_nacimiento",
                    "telefono",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datos Adicionales", {"fields": ("rol", "activo", "fecha_creacion")}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = "Nombre Completo"


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("get_usuario", "get_email")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")

    def get_usuario(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.email

    get_usuario.short_description = "Cliente"

    def get_email(self, obj):
        return obj.usuario.email

    get_email.short_description = "Email"


@admin.register(Admin)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ("get_usuario", "get_email")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")

    def get_usuario(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.email

    get_usuario.short_description = "Admin"

    def get_email(self, obj):
        return obj.usuario.email

    get_email.short_description = "Email"


@admin.register(Recepcionista)
class RecepcionistaAdmin(admin.ModelAdmin):
    list_display = ("get_usuario", "get_email")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")

    def get_usuario(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.email

    get_usuario.short_description = "Recepcionista"

    def get_email(self, obj):
        return obj.usuario.email

    get_email.short_description = "Email"
