from django.urls import path

from . import views

urlpatterns = [
    path("", views.signin, name="signin"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/<str:section>/", views.dashboard, name="staff_page"),
    path("signout/", views.signout, name="signout"),
    path(
        "notificaciones/leer/",
        views.mark_notifications_read,
        name="mark_notifications_read",
    ),
    path("usuarios/<int:user_id>/estado/", views.toggle_user, name="toggle_user"),
    path("usuarios/crear/", views.create_managed_user, name="create_managed_user"),
    path(
        "usuarios/<int:user_id>/eliminar/",
        views.delete_managed_user,
        name="delete_managed_user",
    ),
]
