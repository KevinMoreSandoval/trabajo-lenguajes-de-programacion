from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from authentication.views import (
    _is_staff_role,
    _notify,
    _reservation_redirect,
    _role_name,
)


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def remove_cart_item(request, item_key):
    cart = request.session.get("reservation_cart", [])
    new_cart = [item for item in cart if item.get("key") != item_key]
    request.session["reservation_cart"] = new_cart
    request.session.modified = True
    messages.success(request, "Reserva retirada del carrito.")
    return redirect("dashboard")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
@transaction.atomic
def checkout_cart(request):
    """Confirma y paga todas las reservas guardadas en el carrito del cliente."""
    from canchas.models import Cancha
    from reservas.models import Reserva, EstadoReserva
    from pagos.models import Pago, MetodoPago, EstadoPago

    if _role_name(request.user) != "Cliente":
        messages.error(request, "El carrito está disponible únicamente para clientes.")
        return redirect("dashboard")
    cart = request.session.get("reservation_cart", [])
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("dashboard")
    metodo = MetodoPago.objects.filter(
        pk=request.POST.get("metodo_pago_id"), activo=True
    ).first()
    if not metodo or metodo.nombre.lower() not in ("yape", "plin", "tunki"):
        messages.error(request, "Selecciona Yape, Plin o Tunki para pagar el carrito.")
        return redirect("dashboard")
    codigo = request.POST.get("codigo_operacion", "").strip()
    reference = request.POST.get("referencia", "").strip()[:100]
    observation = request.POST.get("observacion", "").strip()[:255]
    if len(codigo) < 4:
        messages.error(request, "Ingresa el código de operación de la billetera.")
        return redirect("dashboard")

    estado_reserva, _ = EstadoReserva.objects.get_or_create(nombre="Confirmada")
    estado_pago, _ = EstadoPago.objects.get_or_create(nombre="Completado")
    prepared = []
    for item in cart:
        cancha = Cancha.objects.get(pk=item["cancha_id"])
        fecha = datetime.strptime(item["fecha"], "%Y-%m-%d").date()
        inicio = datetime.strptime(item["hora_inicio"], "%H:%M").time()
        fin = datetime.strptime(item["hora_fin"], "%H:%M").time()
        occupied = (
            Reserva.objects.select_for_update()
            .filter(
                cancha=cancha,
                fecha=fecha,
                hora_inicio__lt=fin,
                hora_fin__gt=inicio,
            )
            .exclude(estado__nombre__iexact="Cancelada")
            .exists()
        )
        if occupied:
            messages.error(
                request,
                f'{cancha.nombre} ya no está disponible el {item["fecha"]} de {item["hora_inicio"]} a {item["hora_fin"]}.',
            )
            return redirect("dashboard")
        prepared.append((item, cancha, fecha, inicio, fin))

    created = []
    for item, cancha, fecha, inicio, fin in prepared:
        monto = Decimal(item["monto"])
        reserva = Reserva.objects.create(
            cancha=cancha,
            cliente=request.user,
            estado=estado_reserva,
            fecha=fecha,
            hora_inicio=inicio,
            hora_fin=fin,
            duracion_horas=Decimal(item["duracion"]),
            monto_total=monto,
            monto_pagado=monto,
            observaciones=item.get("observaciones", ""),
        )
        Pago.objects.create(
            reserva=reserva,
            metodo_pago=metodo,
            estado_pago=estado_pago,
            monto=monto,
            codigo_operacion=codigo,
            referencia=reference,
            observacion=observation or f"Pago conjunto de carrito con {metodo.nombre}",
        )
        _notify(
            request.user,
            reserva,
            f"Pago de S/ {monto} confirmado para la reserva #{reserva.pk}.",
            "Pago confirmado",
        )
        created.append(reserva.pk)

    request.session["reservation_cart"] = []
    request.session.modified = True
    total = sum((Decimal(item["monto"]) for item in cart), Decimal("0.00"))
    messages.success(
        request, f"Pago de S/ {total} confirmado. Se crearon {len(created)} reservas."
    )
    for reservation_id in created:
        reservation = Reserva.objects.get(pk=reservation_id)
        _notify(
            request.user,
            reservation,
            f"Reserva #{reservation_id} confirmada y pagada dentro de tu compra.",
            "Compra confirmada",
        )
    return redirect("dashboard")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
@transaction.atomic
def pay_reservation(request, reservation_id):
    """Registra el pago total o parcial de una reserva autorizada."""
    from reservas.models import Reserva, EstadoReserva
    from pagos.models import Pago, MetodoPago, EstadoPago

    reserva = Reserva.objects.select_for_update().filter(pk=reservation_id).first()
    if not reserva or (
        not _is_staff_role(request.user) and reserva.cliente_id != request.user.id
    ):
        messages.error(request, "No tienes permiso para pagar esta reserva.")
        return _reservation_redirect(request)

    saldo = reserva.monto_total - reserva.monto_pagado
    try:
        monto = Decimal(request.POST.get("monto") or saldo).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        monto = Decimal("0")
    metodo = MetodoPago.objects.filter(
        pk=request.POST.get("metodo_pago_id"), activo=True
    ).first()
    if not metodo or monto <= 0 or monto > saldo:
        messages.error(request, "El método o monto de pago no es válido.")
        return _reservation_redirect(request)
    codigo_operacion = request.POST.get("codigo_operacion", "").strip()[:100]
    if metodo.nombre.lower() != "efectivo" and not codigo_operacion:
        messages.error(
            request, f"Ingresa el código de operación del pago con {metodo.nombre}."
        )
        return _reservation_redirect(request)

    estado_pago, _ = EstadoPago.objects.get_or_create(nombre="Completado")
    pago = Pago.objects.create(
        reserva=reserva,
        metodo_pago=metodo,
        estado_pago=estado_pago,
        monto=monto,
        codigo_operacion=codigo_operacion,
        observacion=request.POST.get("observacion", "").strip()[:255],
    )
    reserva.monto_pagado += monto
    if reserva.monto_pagado >= reserva.monto_total:
        reserva.estado, _ = EstadoReserva.objects.get_or_create(nombre="Confirmada")
    reserva.save(update_fields=["monto_pagado", "estado"])
    messages.success(
        request, f"Pago de S/ {monto} registrado en la reserva #{reserva.pk}."
    )
    from boletas.views import payment_receipt_response

    return payment_receipt_response(pago)
