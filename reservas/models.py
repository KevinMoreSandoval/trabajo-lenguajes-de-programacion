from django.conf import settings
from django.db import models


class EstadoReserva(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "estados_reservas"
        verbose_name = "Estado de reserva"
        verbose_name_plural = "Estados de reservas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Reserva(models.Model):
    cancha = models.ForeignKey(
        "canchas.Cancha",
        on_delete=models.RESTRICT,
        db_column="cancha_id",
        related_name="reservas",
    )
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        db_column="cliente_id",
        related_name="reservas",
    )
    estado = models.ForeignKey(
        EstadoReserva,
        on_delete=models.RESTRICT,
        db_column="estado_id",
        related_name="reservas",
    )

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    hora_llegada = models.TimeField(null=True, blank=True)
    duracion_horas = models.DecimalField(max_digits=4, decimal_places=2)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observaciones = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reservas"
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"Reserva {self.pk} - {self.cancha} ({self.fecha})"


class TipoNotificacion(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "tipos_notificaciones"
        verbose_name = "Tipo de notificación"
        verbose_name_plural = "Tipos de notificaciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Notificacion(models.Model):
    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        db_column="reserva_id",
        related_name="notificaciones",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="usuario_id",
        related_name="notificaciones",
    )
    tipo = models.ForeignKey(
        TipoNotificacion,
        on_delete=models.RESTRICT,
        db_column="tipo_id",
        related_name="notificaciones",
    )

    mensaje = models.TextField()
    asunto = models.CharField(max_length=255, null=True, blank=True)
    leida = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificaciones"
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_envio"]

    def __str__(self):
        return f"Notificación {self.pk} - {self.usuario.email}"


class NotificacionEmail(models.Model):
    notificacion = models.OneToOneField(
        Notificacion,
        on_delete=models.CASCADE,
        db_column="notificacion_id",
        primary_key=True,
        related_name="notificacion_email",
    )
    destinatario = models.EmailField()

    class Meta:
        db_table = "notificaciones_email"
        verbose_name = "Notificación Email"
        verbose_name_plural = "Notificaciones Email"

    def __str__(self):
        return f"Email: {self.destinatario}"


class NotificacionSMS(models.Model):
    notificacion = models.OneToOneField(
        Notificacion,
        on_delete=models.CASCADE,
        db_column="notificacion_id",
        primary_key=True,
        related_name="notificacion_sms",
    )
    numero_telefono = models.CharField(max_length=20)

    class Meta:
        db_table = "notificaciones_sms"
        verbose_name = "Notificación SMS"
        verbose_name_plural = "Notificaciones SMS"

    def __str__(self):
        return f"SMS: {self.numero_telefono}"


class NotificacionPush(models.Model):
    notificacion = models.OneToOneField(
        Notificacion,
        on_delete=models.CASCADE,
        db_column="notificacion_id",
        primary_key=True,
        related_name="notificacion_push",
    )
    token_dispositivo = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "notificaciones_push"
        verbose_name = "Notificación Push"
        verbose_name_plural = "Notificaciones Push"

    def __str__(self):
        return f"Push: {self.notificacion.usuario.email}"
