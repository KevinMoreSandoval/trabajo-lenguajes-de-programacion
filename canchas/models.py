from django.db import models

class EstadoCancha(models.Model):
    nombre = models.CharField(max_length=50)
    class Meta:
        db_table = 'estados_canchas'

class Regla(models.Model):
    nombre = models.CharField(max_length=150)
    class Meta:
        db_table = 'reglas'

class Cancha(models.Model):
    estado = models.ForeignKey(EstadoCancha, on_delete=models.RESTRICT, db_column='estado_id')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    capacidad = models.IntegerField()
    precio_por_hora = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.CharField(max_length=255)
    imagen_url = models.CharField(max_length=255, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    techada = models.BooleanField(default=False)
    iluminacion = models.BooleanField(default=False)
    banos = models.BooleanField(default=False)
    ancho = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    largo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    reglas = models.ManyToManyField(Regla, db_table='canchas_reglas')

    class Meta:
        db_table = 'canchas'

class HorarioBloqueado(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, db_column='cancha_id')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    motivo = models.CharField(max_length=255, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'horarios_bloqueados'