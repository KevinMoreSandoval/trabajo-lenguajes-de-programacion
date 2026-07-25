from django.urls import path

from . import views

app_name = 'pagos'

urlpatterns = [
    path('reserva/<int:reserva_id>/', views.pagar_reserva, name='pagar_reserva'),
    path('reserva/<int:reserva_id>/cancelar/', views.cancelar_pago, name='cancelar_pago'),
]
