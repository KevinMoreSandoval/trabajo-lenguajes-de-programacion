from django.contrib import admin

from .models import Cancha, EstadoCancha, HorarioBloqueado, Regla


@admin.register(EstadoCancha)
class EstadoCanchaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Regla)
class ReglaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo', 'estado', 'capacidad', 'precio_por_hora', 'ubicacion')
    list_filter = ('estado', 'tipo', 'techada', 'iluminacion', 'banos')
    search_fields = ('nombre', 'tipo', 'ubicacion')
    filter_horizontal = ('reglas',)


@admin.register(HorarioBloqueado)
class HorarioBloqueadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cancha', 'fecha', 'hora_inicio', 'hora_fin', 'motivo')
    list_filter = ('fecha', 'cancha')
    search_fields = ('cancha__nombre', 'motivo')
