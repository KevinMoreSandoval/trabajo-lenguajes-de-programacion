from django.contrib import admin
from .models import (
    EstadoPago,
    TipoMetodoPago,
    MetodoPago,
    Pago,
    PagoTarjeta,
    PagoBilletera,
)


@admin.register(EstadoPago)
class EstadoPagoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(TipoMetodoPago)
class TipoMetodoPagoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("nombre",)
    ordering = ("nombre",)
    fieldsets = (("Información", {"fields": ("nombre", "tipo", "activo")}),)


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "reserva",
        "monto",
        "estado_pago",
        "metodo_pago",
        "fecha_pago",
    )
    list_filter = ("estado_pago", "metodo_pago", "fecha_pago")
    search_fields = ("reserva__pk", "codigo_operacion", "referencia")
    ordering = ("-fecha_pago",)
    fieldsets = (
        ("Información de Reserva", {"fields": ("reserva",)}),
        ("Datos del Pago", {"fields": ("monto", "estado_pago", "metodo_pago")}),
        (
            "Detalles",
            {
                "fields": (
                    "referencia",
                    "codigo_operacion",
                    "comprobante_url",
                    "observacion",
                )
            },
        ),
    )
    readonly_fields = ("fecha_pago",)


@admin.register(PagoTarjeta)
class PagoTarjetaAdmin(admin.ModelAdmin):
    list_display = ("pago", "banco", "ultimos_digitos")
    list_filter = ("banco",)
    search_fields = ("pago__pk", "banco", "numero_tarjeta")
    fieldsets = (
        ("Información", {"fields": ("pago",)}),
        (
            "Detalles de Tarjeta",
            {"fields": ("numero_tarjeta", "banco", "ultimos_digitos")},
        ),
    )


@admin.register(PagoBilletera)
class PagoBilleteraAdmin(admin.ModelAdmin):
    list_display = ("pago", "billetera", "numero_cuenta")
    list_filter = ("billetera",)
    search_fields = ("pago__pk", "billetera", "numero_cuenta")
    fieldsets = (
        ("Información", {"fields": ("pago",)}),
        ("Detalles de Billetera", {"fields": ("billetera", "numero_cuenta")}),
    )
