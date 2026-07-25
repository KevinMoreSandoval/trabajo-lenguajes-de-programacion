from django.db import models


class EstadoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "estados_pagos"
        verbose_name = "Estado de pago"
        verbose_name_plural = "Estados de pagos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class TipoMetodoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "tipos_metodos_pago"
        verbose_name = "Tipo de método de pago"
        verbose_name_plural = "Tipos de métodos de pago"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class MetodoPago(models.Model):
    tipo = models.ForeignKey(
        TipoMetodoPago,
        on_delete=models.RESTRICT,
        db_column="tipo_id",
        related_name="metodos",
    )
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "metodos_pago"
        verbose_name = "Método de pago"
        verbose_name_plural = "Métodos de pago"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.CASCADE,
        db_column="reserva_id",
        related_name="pagos",
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.RESTRICT,
        db_column="metodo_pago_id",
        related_name="pagos",
    )
    estado_pago = models.ForeignKey(
        EstadoPago,
        on_delete=models.RESTRICT,
        db_column="estado_pago_id",
        related_name="pagos",
    )

    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=100, null=True, blank=True)
    codigo_operacion = models.CharField(max_length=100, null=True, blank=True)
    comprobante_url = models.CharField(max_length=255, null=True, blank=True)
    observacion = models.CharField(max_length=255, null=True, blank=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pagos"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_pago"]

    def __str__(self):
        return f"Pago {self.pk} - {self.monto}"


class PagoTarjeta(models.Model):
    pago = models.OneToOneField(
        Pago,
        on_delete=models.CASCADE,
        db_column="pago_id",
        primary_key=True,
        related_name="pago_tarjeta",
    )
    numero_tarjeta = models.CharField(max_length=50, null=True, blank=True)
    banco = models.CharField(max_length=100, null=True, blank=True)
    ultimos_digitos = models.CharField(max_length=4, null=True, blank=True)

    class Meta:
        db_table = "pagos_tarjeta"
        verbose_name = "Pago con Tarjeta"
        verbose_name_plural = "Pagos con Tarjeta"

    def __str__(self):
        return f"Pago Tarjeta: {self.pago.monto}"


class PagoBilletera(models.Model):
    pago = models.OneToOneField(
        Pago,
        on_delete=models.CASCADE,
        db_column="pago_id",
        primary_key=True,
        related_name="pago_billetera",
    )
    billetera = models.CharField(max_length=100, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "pagos_billetera"
        verbose_name = "Pago con Billetera"
        verbose_name_plural = "Pagos con Billetera"

    def __str__(self):
        return f"Pago Billetera: {self.pago.monto}"
