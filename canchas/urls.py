from django.urls import path

from . import views

urlpatterns = [
    path("canchas/crear/", views.create_court, name="create_court"),
    path("horarios/crear/", views.create_schedule, name="create_schedule"),
    path(
        "canchas/<int:court_id>/estado/",
        views.update_court_status,
        name="update_court_status",
    ),
    path(
        "canchas/disponibilidad/", views.court_availability, name="court_availability"
    ),
]
