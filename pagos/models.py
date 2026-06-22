from django.db import models

class EstadoPago(models.Model):
    nombre = models.CharField(max_length=50)
    class Meta:
        db_table = 'estados_pagos'

class TipoMetodoPago(models.Model):
    nombre = models.CharField(max_length=50)
    class Meta:
        db_table = 'tipos_metodos_pago'

class MetodoPago(models.Model):
    tipo = models.ForeignKey(TipoMetodoPago, on_delete=models.RESTRICT, db_column='tipo_id')
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'metodos_pago'

class Pago(models.Model):
    reserva = models.ForeignKey('reservas.Reserva', on_delete=models.CASCADE, db_column='reserva_id')
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.RESTRICT, db_column='metodo_pago_id')
    estado_pago = models.ForeignKey(EstadoPago, on_delete=models.RESTRICT, db_column='estado_pago_id')
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=100, null=True, blank=True)
    codigo_operacion = models.CharField(max_length=100, null=True, blank=True)
    comprobante_url = models.CharField(max_length=255, null=True, blank=True)
    observacion = models.CharField(max_length=255, null=True, blank=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos'