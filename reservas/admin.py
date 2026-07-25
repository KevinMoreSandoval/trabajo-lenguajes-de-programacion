from django.contrib import admin

from .models import EstadoReserva, Reserva


@admin.register(EstadoReserva)
class EstadoReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cancha', 'cliente', 'estado', 'fecha', 'hora_inicio', 'hora_fin', 'monto_total', 'monto_pagado')
    list_filter = ('estado', 'fecha', 'cancha')
    search_fields = ('cancha__nombre', 'cliente__email', 'cliente__first_name', 'cliente__last_name')
    date_hierarchy = 'fecha'
