from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from canchas.models import Cancha, EstadoCancha, Horario, Regla


class Command(BaseCommand):
    help = "Crea o actualiza el catálogo inicial de canchas y sus horarios."

    CANCHAS = [
        {
            "nombre": "Fútbol 5",
            "tipo": "Fútbol 5",
            "capacidad": 10,
            "precio_por_hora": "30.00",
            "ubicacion": "Zona deportiva A - primer nivel",
            "descripcion": "Cancha de césped sintético para partidos de fútbol 5. Incluye arcos, mallas de protección, iluminación LED y zona de descanso.",
            "imagen_url": "/static/img/courts/futbol-5.jpeg",
            "techada": False,
            "iluminacion": True,
            "banos": True,
            "ancho": "20.00",
            "largo": "30.00",
            "reglas": [
                "Usar zapatillas adecuadas para césped sintético",
                "Presentarse 10 minutos antes de la reserva",
            ],
        },
        {
            "nombre": "Fútbol 11",
            "tipo": "Fútbol 11",
            "capacidad": 22,
            "precio_por_hora": "80.00",
            "ubicacion": "Zona deportiva B - campo principal",
            "descripcion": "Campo reglamentario de fútbol 11 con césped sintético, arcos profesionales, reflectores LED, bancas para suplentes y vestuarios.",
            "imagen_url": "/static/img/courts/futbol-11.jpeg",
            "techada": False,
            "iluminacion": True,
            "banos": True,
            "ancho": "45.00",
            "largo": "90.00",
            "reglas": [
                "Máximo 22 jugadores en cancha",
                "No ingresar alimentos al campo",
            ],
        },
        {
            "nombre": "Vóley Central",
            "tipo": "Vóley",
            "capacidad": 12,
            "precio_por_hora": "40.00",
            "ubicacion": "Coliseo techado - segundo nivel",
            "descripcion": "Cancha techada de vóley con piso deportivo, red regulable, iluminación uniforme, marcador y graderías laterales.",
            "imagen_url": "/static/img/courts/voley.jpeg",
            "techada": True,
            "iluminacion": True,
            "banos": True,
            "ancho": "9.00",
            "largo": "18.00",
            "reglas": ["Usar calzado deportivo limpio", "No colgarse de la red"],
        },
        {
            "nombre": "Básquet Arena",
            "tipo": "Básquet",
            "capacidad": 10,
            "precio_por_hora": "45.00",
            "ubicacion": "Coliseo techado - primer nivel",
            "descripcion": "Cancha de básquet con piso de alto rendimiento, canastas profesionales, tablero acrílico, marcador digital e iluminación LED.",
            "imagen_url": "/static/img/courts/basket.jpeg",
            "techada": True,
            "iluminacion": True,
            "banos": True,
            "ancho": "15.00",
            "largo": "28.00",
            "reglas": [
                "Usar calzado con suela que no marque",
                "Prohibido mover las canastas",
            ],
        },
        {
            "nombre": "Cancha Multiuso",
            "tipo": "Multiuso",
            "capacidad": 16,
            "precio_por_hora": "35.00",
            "ubicacion": "Zona deportiva C - patio principal",
            "descripcion": "Espacio multiuso adaptable para fulbito, vóley y actividades recreativas. Cuenta con iluminación, baños y equipamiento básico.",
            "imagen_url": "/static/img/courts/multiuso.jpeg",
            "techada": False,
            "iluminacion": True,
            "banos": True,
            "ancho": "18.00",
            "largo": "32.00",
            "reglas": [
                "Solicitar el equipamiento al recepcionista",
                "Dejar la cancha limpia al finalizar",
            ],
        },
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        disponible, _ = EstadoCancha.objects.get_or_create(nombre="Disponible")
        total_horarios = 0

        for data in self.CANCHAS:
            reglas = data.pop("reglas")
            cancha, created = Cancha.objects.update_or_create(
                nombre=data["nombre"],
                defaults={**data, "estado": disponible},
            )
            cancha.reglas.set(
                [Regla.objects.get_or_create(nombre=nombre)[0] for nombre in reglas]
            )

            # Disponibilidad de 08:00 a 22:00 en bloques seleccionables de 30 minutos.
            Horario.objects.filter(cancha=cancha).delete()
            for hour in range(8, 22):
                Horario.objects.create(
                    cancha=cancha, hora_inicio=time(hour, 0), hora_fin=time(hour, 30)
                )
                Horario.objects.create(
                    cancha=cancha,
                    hora_inicio=time(hour, 30),
                    hora_fin=time(hour + 1, 0),
                )
                total_horarios += 2

            action = "Creada" if created else "Actualizada"
            self.stdout.write(self.style.SUCCESS(f"{action}: {cancha.nombre}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo listo: {len(self.CANCHAS)} canchas y {total_horarios} bloques horarios."
            )
        )
