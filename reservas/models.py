from django.db import models

class EstadoReserva(models.Model):
    nombre = models.CharField(max_length=50)
    class Meta:
        db_table = 'estados_reservas'

class ReservaGrupo(models.Model):
    cliente = models.ForeignKey('authentication.Usuario', on_delete=models.RESTRICT, db_column='cliente_id')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total_general = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, default='pendiente')

    class Meta:
        db_table = 'reservas_grupos'

class Reserva(models.Model):
    grupo = models.ForeignKey(ReservaGrupo, on_delete=models.CASCADE, null=True, blank=True, related_name='reservas', db_column='grupo_id')
    cancha = models.ForeignKey('canchas.Cancha', on_delete=models.RESTRICT, db_column='cancha_id')
    cliente = models.ForeignKey('authentication.Usuario', on_delete=models.RESTRICT, db_column='cliente_id')
    estado = models.ForeignKey(EstadoReserva, on_delete=models.RESTRICT, db_column='estado_id')
    
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    hora_llegada = models.TimeField(null=True, blank=True)
    duracion_horas = models.DecimalField(max_digits=4, decimal_places=2)
    duracion_minutos = models.PositiveIntegerField(null=True, blank=True)
    precio_por_hora = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observaciones = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservas'
