from django.urls import path

from . import views

urlpatterns = [
    path(
        "reservas/<int:reservation_id>/pagar/",
        views.pay_reservation,
        name="pay_reservation",
    ),
    path(
        "carrito/quitar/<str:item_key>/",
        views.remove_cart_item,
        name="remove_cart_item",
    ),
    path("carrito/pagar/", views.checkout_cart, name="checkout_cart"),
]
