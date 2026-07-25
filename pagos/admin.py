from django.contrib import admin

from .models import EstadoPago, MetodoPago, Pago, TipoMetodoPago


@admin.register(EstadoPago)
class EstadoPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(TipoMetodoPago)
class TipoMetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo', 'activo')
    list_filter = ('activo', 'tipo')
    search_fields = ('nombre',)


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'reserva', 'metodo_pago', 'estado_pago', 'monto', 'fecha_pago')
    list_filter = ('estado_pago', 'metodo_pago', 'fecha_pago')
    search_fields = ('reserva__cancha__nombre', 'reserva__cliente__email', 'referencia', 'codigo_operacion')
