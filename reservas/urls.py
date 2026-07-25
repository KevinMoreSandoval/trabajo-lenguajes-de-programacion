from django.urls import path

from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.mis_reservas, name='mis_reservas'),
    path('carrito/', views.carrito_reservas, name='carrito'),
    path('recepcion/buscar-cliente/', views.recepcion_buscar_cliente, name='recepcion_buscar_cliente'),
    path('recepcion/crear/', views.recepcion_crear_reserva, name='recepcion_crear'),
    path('crear/<int:cancha_id>/', views.crear_reserva, name='crear'),
    path('<int:reserva_id>/confirmada/', views.reserva_confirmada, name='confirmada'),
    path('<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar'),
    path('<int:reserva_id>/confirmar/', views.confirmar_reserva, name='confirmar'),
    path('<int:reserva_id>/finalizar/', views.finalizar_reserva, name='finalizar'),
]
