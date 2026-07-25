from django.contrib import admin
from .models import (
    EstadoReserva,
    Reserva,
    TipoNotificacion,
    Notificacion,
    NotificacionEmail,
    NotificacionSMS,
    NotificacionPush,
)


@admin.register(EstadoReserva)
class EstadoReservaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "cancha",
        "cliente",
        "estado",
        "fecha",
        "hora_inicio",
        "monto_total",
        "monto_pagado",
    )
    list_filter = ("estado", "fecha", "cancha")
    search_fields = (
        "cancha__nombre",
        "cliente__email",
        "cliente__first_name",
        "cliente__last_name",
    )
    ordering = ("-fecha_creacion",)
    fieldsets = (
        ("Información de Reserva", {"fields": ("cancha", "cliente", "estado")}),
        (
            "Fecha y Hora",
            {"fields": ("fecha", "hora_inicio", "hora_fin", "hora_llegada")},
        ),
        (
            "Detalles",
            {
                "fields": (
                    "duracion_horas",
                    "monto_total",
                    "monto_pagado",
                    "observaciones",
                )
            },
        ),
    )
    readonly_fields = ("fecha_creacion",)


@admin.register(TipoNotificacion)
class TipoNotificacionAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "usuario",
        "reserva",
        "tipo",
        "asunto",
        "leida",
        "fecha_envio",
    )
    list_filter = ("tipo", "leida", "fecha_envio")
    search_fields = (
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "asunto",
        "mensaje",
    )
    ordering = ("-fecha_envio",)
    fieldsets = (
        ("Información", {"fields": ("usuario", "reserva", "tipo")}),
        ("Contenido", {"fields": ("asunto", "mensaje")}),
        ("Estado", {"fields": ("leida",)}),
    )
    readonly_fields = ("fecha_envio",)


@admin.register(NotificacionEmail)
class NotificacionEmailAdmin(admin.ModelAdmin):
    list_display = ("notificacion", "destinatario")
    search_fields = ("notificacion__usuario__email", "destinatario")
    fieldsets = (
        ("Información", {"fields": ("notificacion",)}),
        ("Destinatario", {"fields": ("destinatario",)}),
    )


@admin.register(NotificacionSMS)
class NotificacionSMSAdmin(admin.ModelAdmin):
    list_display = ("notificacion", "numero_telefono")
    search_fields = ("notificacion__usuario__email", "numero_telefono")
    fieldsets = (
        ("Información", {"fields": ("notificacion",)}),
        ("Teléfono", {"fields": ("numero_telefono",)}),
    )


@admin.register(NotificacionPush)
class NotificacionPushAdmin(admin.ModelAdmin):
    list_display = ("notificacion", "token_dispositivo")
    search_fields = ("notificacion__usuario__email", "token_dispositivo")
    fieldsets = (
        ("Información", {"fields": ("notificacion",)}),
        ("Dispositivo", {"fields": ("token_dispositivo",)}),
    )
