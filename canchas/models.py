from django.db import models


class EstadoCancha(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "estados_canchas"
        verbose_name = "Estado de cancha"
        verbose_name_plural = "Estados de canchas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Regla(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = "reglas"
        verbose_name = "Regla"
        verbose_name_plural = "Reglas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Cancha(models.Model):
    estado = models.ForeignKey(
        EstadoCancha,
        on_delete=models.RESTRICT,
        db_column="estado_id",
        related_name="canchas",
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    capacidad = models.IntegerField()
    precio_por_hora = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.CharField(max_length=255)
    imagen_url = models.CharField(max_length=255, null=True, blank=True)
    imagen = models.FileField(upload_to="canchas/", null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    techada = models.BooleanField(default=False)
    iluminacion = models.BooleanField(default=False)
    banos = models.BooleanField(default=False)
    ancho = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    largo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    reglas = models.ManyToManyField(
        Regla, related_name="canchas", db_table="canchas_reglas"
    )

    class Meta:
        db_table = "canchas"
        verbose_name = "Cancha"
        verbose_name_plural = "Canchas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def imagen_src(self):
        return self.imagen.url if self.imagen else self.imagen_url


class CanchaValley(models.Model):
    cancha = models.OneToOneField(
        Cancha,
        on_delete=models.CASCADE,
        db_column="cancha_id",
        primary_key=True,
        related_name="cancha_valley",
    )
    tipo_superficie = models.CharField(max_length=50, null=True, blank=True)
    altura_red = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = "canchas_valley"
        verbose_name = "Cancha de Voleibol"
        verbose_name_plural = "Canchas de Voleibol"

    def __str__(self):
        return f"Voleibol: {self.cancha.nombre}"


class CanchaBasket(models.Model):
    cancha = models.OneToOneField(
        Cancha,
        on_delete=models.CASCADE,
        db_column="cancha_id",
        primary_key=True,
        related_name="cancha_basket",
    )
    canastas_profesional = models.BooleanField(default=False)
    marcador_digital = models.BooleanField(default=False)

    class Meta:
        db_table = "canchas_basket"
        verbose_name = "Cancha de Basquetbol"
        verbose_name_plural = "Canchas de Basquetbol"

    def __str__(self):
        return f"Basquetbol: {self.cancha.nombre}"


class CanchaFutbol(models.Model):
    cancha = models.OneToOneField(
        Cancha,
        on_delete=models.CASCADE,
        db_column="cancha_id",
        primary_key=True,
        related_name="cancha_futbol",
    )
    tipo_cesped = models.CharField(max_length=50, null=True, blank=True)
    arcos_profesional = models.BooleanField(default=False)

    class Meta:
        db_table = "canchas_futbol"
        verbose_name = "Cancha de Fútbol"
        verbose_name_plural = "Canchas de Fútbol"

    def __str__(self):
        return f"Fútbol: {self.cancha.nombre}"


class Horario(models.Model):
    cancha = models.ForeignKey(
        Cancha,
        on_delete=models.CASCADE,
        db_column="cancha_id",
        related_name="horarios",
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = "horarios"
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ["hora_inicio"]

    def __str__(self):
        return f"{self.cancha.nombre} - {self.hora_inicio} a {self.hora_fin}"


class HorarioManana(models.Model):
    horario = models.OneToOneField(
        Horario,
        on_delete=models.CASCADE,
        db_column="horario_id",
        primary_key=True,
        related_name="horario_manana",
    )

    class Meta:
        db_table = "horarios_manana"
        verbose_name = "Horario Mañana"
        verbose_name_plural = "Horarios Mañana"

    def __str__(self):
        return f"Mañana: {self.horario}"


class HorarioTarde(models.Model):
    horario = models.OneToOneField(
        Horario,
        on_delete=models.CASCADE,
        db_column="horario_id",
        primary_key=True,
        related_name="horario_tarde",
    )

    class Meta:
        db_table = "horarios_tarde"
        verbose_name = "Horario Tarde"
        verbose_name_plural = "Horarios Tarde"

    def __str__(self):
        return f"Tarde: {self.horario}"


class HorarioNoche(models.Model):
    horario = models.OneToOneField(
        Horario,
        on_delete=models.CASCADE,
        db_column="horario_id",
        primary_key=True,
        related_name="horario_noche",
    )

    class Meta:
        db_table = "horarios_noche"
        verbose_name = "Horario Noche"
        verbose_name_plural = "Horarios Noche"

    def __str__(self):
        return f"Noche: {self.horario}"


class HorarioBloqueado(models.Model):
    cancha = models.ForeignKey(
        Cancha,
        on_delete=models.CASCADE,
        db_column="cancha_id",
        related_name="horarios_bloqueados",
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    motivo = models.CharField(max_length=255, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "horarios_bloqueados"
        verbose_name = "Horario bloqueado"
        verbose_name_plural = "Horarios bloqueados"
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"{self.cancha} - {self.fecha} {self.hora_inicio}-{self.hora_fin}"
