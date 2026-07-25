from django.contrib import admin
from .models import (
    EstadoCancha,
    Regla,
    Cancha,
    CanchaValley,
    CanchaBasket,
    CanchaFutbol,
    Horario,
    HorarioManana,
    HorarioTarde,
    HorarioNoche,
    HorarioBloqueado,
)


@admin.register(EstadoCancha)
class EstadoCanchaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(Regla)
class ReglaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "tipo",
        "estado",
        "precio_por_hora",
        "capacidad",
        "fecha_creacion",
    )
    list_filter = (
        "estado",
        "tipo",
        "fecha_creacion",
        "techada",
        "iluminacion",
        "banos",
    )
    search_fields = ("nombre", "ubicacion", "descripcion")
    ordering = ("nombre",)
    fieldsets = (
        (
            "Información Básica",
            {"fields": ("nombre", "tipo", "estado", "ubicacion", "descripcion")},
        ),
        (
            "Características",
            {
                "fields": (
                    "capacidad",
                    "techada",
                    "iluminacion",
                    "banos",
                    "ancho",
                    "largo",
                )
            },
        ),
        ("Precio", {"fields": ("precio_por_hora",)}),
        ("Multimedia", {"fields": ("imagen_url",)}),
        ("Reglas", {"fields": ("reglas",)}),
    )


@admin.register(CanchaValley)
class CanchaValleyAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "tipo_superficie", "altura_red")
    search_fields = ("cancha__nombre",)

    def get_cancha(self, obj):
        return obj.cancha.nombre

    get_cancha.short_description = "Cancha"


@admin.register(CanchaBasket)
class CanchaBasketAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "canastas_profesional", "marcador_digital")
    search_fields = ("cancha__nombre",)

    def get_cancha(self, obj):
        return obj.cancha.nombre

    get_cancha.short_description = "Cancha"


@admin.register(CanchaFutbol)
class CanchaFutbolAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "tipo_cesped", "arcos_profesional")
    search_fields = ("cancha__nombre",)

    def get_cancha(self, obj):
        return obj.cancha.nombre

    get_cancha.short_description = "Cancha"


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "hora_inicio", "hora_fin")
    list_filter = ("cancha", "hora_inicio")
    search_fields = ("cancha__nombre",)
    ordering = ("cancha", "hora_inicio")

    def get_cancha(self, obj):
        return obj.cancha.nombre

    get_cancha.short_description = "Cancha"


@admin.register(HorarioManana)
class HorarioMananaAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "get_hora_inicio", "get_hora_fin")
    search_fields = ("horario__cancha__nombre",)

    def get_cancha(self, obj):
        return obj.horario.cancha.nombre

    get_cancha.short_description = "Cancha"

    def get_hora_inicio(self, obj):
        return obj.horario.hora_inicio

    get_hora_inicio.short_description = "Hora Inicio"

    def get_hora_fin(self, obj):
        return obj.horario.hora_fin

    get_hora_fin.short_description = "Hora Fin"


@admin.register(HorarioTarde)
class HorarioTardeAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "get_hora_inicio", "get_hora_fin")
    search_fields = ("horario__cancha__nombre",)

    def get_cancha(self, obj):
        return obj.horario.cancha.nombre

    get_cancha.short_description = "Cancha"

    def get_hora_inicio(self, obj):
        return obj.horario.hora_inicio

    get_hora_inicio.short_description = "Hora Inicio"

    def get_hora_fin(self, obj):
        return obj.horario.hora_fin

    get_hora_fin.short_description = "Hora Fin"


@admin.register(HorarioNoche)
class HorarioNocheAdmin(admin.ModelAdmin):
    list_display = ("get_cancha", "get_hora_inicio", "get_hora_fin")
    search_fields = ("horario__cancha__nombre",)

    def get_cancha(self, obj):
        return obj.horario.cancha.nombre

    get_cancha.short_description = "Cancha"

    def get_hora_inicio(self, obj):
        return obj.horario.hora_inicio

    get_hora_inicio.short_description = "Hora Inicio"

    def get_hora_fin(self, obj):
        return obj.horario.hora_fin

    get_hora_fin.short_description = "Hora Fin"


@admin.register(HorarioBloqueado)
class HorarioBloqueadoAdmin(admin.ModelAdmin):
    list_display = ("cancha", "fecha", "hora_inicio", "hora_fin", "motivo")
    list_filter = ("cancha", "fecha")
    search_fields = ("cancha__nombre", "motivo")
    ordering = ("fecha", "hora_inicio")
    fieldsets = (
        ("Información", {"fields": ("cancha", "fecha", "hora_inicio", "hora_fin")}),
        ("Detalles", {"fields": ("motivo",)}),
    )
