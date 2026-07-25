from django.urls import path

from . import views

urlpatterns = [
    path("crear/", views.create_reservation, name="create_reservation"),
    path("horarios-ocupados/", views.occupied_slots, name="occupied_slots"),
    path(
        "<int:reservation_id>/eliminar/",
        views.delete_reservation,
        name="delete_reservation",
    ),
    path(
        "<int:reservation_id>/cancelar/",
        views.cancel_reservation,
        name="cancel_reservation",
    ),
    path(
        "<int:reservation_id>/asistencia/",
        views.update_attendance,
        name="update_attendance",
    ),
]
