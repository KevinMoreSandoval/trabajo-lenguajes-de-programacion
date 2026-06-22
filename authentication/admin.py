from django.contrib import admin
from .models import Rol, Usuario

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    # Mostramos los campos principales, incluyendo el rol y el estado activo
    list_display = ('email', 'username', 'rol', 'is_staff', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'is_staff', 'activo')
    search_fields = ('email', 'username', 'dni')
    ordering = ('-fecha_creacion',)
