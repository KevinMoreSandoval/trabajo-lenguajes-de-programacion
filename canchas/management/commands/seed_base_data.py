from django.core.management.base import BaseCommand
from django.utils import timezone

from authentication.models import Rol
from canchas.models import Cancha, EstadoCancha, HorarioBloqueado, Regla
from pagos.models import EstadoPago, MetodoPago, TipoMetodoPago
from reservas.models import EstadoReserva


class Command(BaseCommand):
    help = 'Crea datos base para reservas de canchas.'

    def handle(self, *args, **options):
        for nombre in Rol.ROLES_VALIDOS:
            Rol.objects.get_or_create(nombre=nombre)

        for nombre in ('Disponible', 'Mantenimiento', 'No disponible'):
            EstadoCancha.objects.get_or_create(nombre=nombre)

        for nombre in ('Pendiente', 'Confirmada', 'Pagada', 'Cancelada', 'Finalizada'):
            EstadoReserva.objects.get_or_create(nombre=nombre)

        for nombre in ('Pendiente', 'Pagado', 'Rechazado'):
            EstadoPago.objects.get_or_create(nombre=nombre)

        tipo_efectivo, _ = TipoMetodoPago.objects.get_or_create(nombre='Efectivo')
        tipo_billetera, _ = TipoMetodoPago.objects.get_or_create(nombre='Billetera digital')
        tipo_tarjeta, _ = TipoMetodoPago.objects.get_or_create(nombre='Tarjeta')

        metodos = (
            ('Efectivo', tipo_efectivo),
            ('Yape', tipo_billetera),
            ('Plin', tipo_billetera),
            ('Mercado Pago', tipo_billetera),
            ('Billetera digital', tipo_billetera),
            ('Tarjeta', tipo_tarjeta),
        )
        for nombre, tipo in metodos:
            MetodoPago.objects.get_or_create(nombre=nombre, defaults={'tipo': tipo, 'activo': True})

        reglas = [
            'Usar zapatillas deportivas dentro de la cancha.',
            'Llegar 10 minutos antes del horario reservado.',
            'No ingresar bebidas alcoholicas al campo.',
            'Cuidar el grass sintetico y las instalaciones.',
            'Cancelar o reprogramar con anticipacion.',
        ]
        reglas_creadas = [Regla.objects.get_or_create(nombre=nombre)[0] for nombre in reglas]

        disponible = EstadoCancha.objects.get(nombre='Disponible')
        mantenimiento = EstadoCancha.objects.get(nombre='Mantenimiento')

        canchas = [
            {
                'nombre': 'Cancha Los Campeones',
                'tipo': 'Futbol 7',
                'capacidad': 14,
                'precio_por_hora': '80.00',
                'ubicacion': 'Zona Norte',
                'imagen_url': 'https://images.unsplash.com/photo-1556056504-5c7696c4c28d?auto=format&fit=crop&w=900&q=80',
                'descripcion': 'Cancha de grass sintetico para partidos rapidos y torneos internos.',
                'techada': False,
                'iluminacion': True,
                'banos': True,
                'ancho': '32.00',
                'largo': '52.00',
                'estado': disponible,
            },
            {
                'nombre': 'Cancha La Bombonera',
                'tipo': 'Futbol 6',
                'capacidad': 12,
                'precio_por_hora': '65.00',
                'ubicacion': 'Av. Principal 450',
                'imagen_url': 'https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=900&q=80',
                'descripcion': 'Espacio compacto con buena iluminacion para reservas nocturnas.',
                'techada': False,
                'iluminacion': True,
                'banos': True,
                'ancho': '28.00',
                'largo': '45.00',
                'estado': disponible,
            },
            {
                'nombre': 'Cancha El Olimpico',
                'tipo': 'Futbol 11',
                'capacidad': 22,
                'precio_por_hora': '150.00',
                'ubicacion': 'Complejo Deportivo Sur',
                'imagen_url': 'https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?auto=format&fit=crop&w=900&q=80',
                'descripcion': 'Cancha amplia para encuentros oficiales y entrenamientos de equipos.',
                'techada': False,
                'iluminacion': True,
                'banos': True,
                'ancho': '68.00',
                'largo': '105.00',
                'estado': disponible,
            },
            {
                'nombre': 'Cancha Techada Sport Center',
                'tipo': 'Futbol 5',
                'capacidad': 10,
                'precio_por_hora': '70.00',
                'ubicacion': 'Jr. Las Palmas 220',
                'imagen_url': 'https://images.unsplash.com/photo-1600679472829-3044539ce8ed?auto=format&fit=crop&w=900&q=80',
                'descripcion': 'Cancha techada ideal para jugar sin depender del clima.',
                'techada': True,
                'iluminacion': True,
                'banos': True,
                'ancho': '20.00',
                'largo': '36.00',
                'estado': disponible,
            },
            {
                'nombre': 'Cancha Barrio Unido',
                'tipo': 'Futbol 7',
                'capacidad': 14,
                'precio_por_hora': '55.00',
                'ubicacion': 'Los Jardines Mz. B',
                'imagen_url': 'https://images.unsplash.com/photo-1517927033932-b3d18e61fb3a?auto=format&fit=crop&w=900&q=80',
                'descripcion': 'Cancha economica para partidos entre amigos y ligas locales.',
                'techada': False,
                'iluminacion': False,
                'banos': True,
                'ancho': '30.00',
                'largo': '50.00',
                'estado': mantenimiento,
            },
        ]

        hoy = timezone.localdate()
        for datos in canchas:
            reglas = datos.pop('reglas', reglas_creadas)
            cancha, _ = Cancha.objects.get_or_create(
                nombre=datos['nombre'],
                defaults=datos,
            )
            cancha.reglas.set(reglas)

            if cancha.estado.nombre == 'Disponible':
                HorarioBloqueado.objects.get_or_create(
                    cancha=cancha,
                    fecha=hoy,
                    hora_inicio='18:00',
                    hora_fin='19:00',
                    defaults={'motivo': 'Reserva de ejemplo'},
                )

        self.stdout.write(self.style.SUCCESS('Datos base creados correctamente.'))
