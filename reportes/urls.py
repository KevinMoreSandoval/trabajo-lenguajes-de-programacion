from django.urls import path

from . import views

urlpatterns = [
    path("reservas.pdf", views.reservations_pdf, name="reservations_pdf"),
]
