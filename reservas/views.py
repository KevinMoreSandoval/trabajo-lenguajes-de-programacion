from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from authentication.views import (
    _is_staff_role,
    _notify,
    _reservation_redirect,
    _role_name,
)
from authentication.models import Usuario


@login_required(login_url="signin")
@require_http_methods(["GET"])
def occupied_slots(request):
    """Devuelve los intervalos ya reservados para una cancha y fecha."""
    from .models import Reserva

    court_id = request.GET.get("cancha")
    date_value = request.GET.get("fecha")
    try:
        date = datetime.strptime(date_value or "", "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"intervalos": []})
    intervals = list(
        Reserva.objects.filter(cancha_id=court_id, fecha=date)
        .exclude(estado__nombre__iexact="Cancelada")
        .values("hora_inicio", "hora_fin")
    )
    return JsonResponse(
        {
            "intervalos": [
                {
                    "inicio": item["hora_inicio"].strftime("%H:%M"),
                    "fin": item["hora_fin"].strftime("%H:%M"),
                }
                for item in intervals
            ]
        }
    )


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
@transaction.atomic
def create_reservation(request):
    """Crea una reserva para el cliente autenticado o para un cliente elegido por recepción."""
    from canchas.models import Cancha
    from reservas.models import Reserva, EstadoReserva

    try:
        cancha = Cancha.objects.select_for_update().get(
            pk=request.POST.get("cancha_id")
        )
        if cancha.estado.nombre != "Disponible":
            messages.error(
                request,
                f"No se puede reservar {cancha.nombre}: está {cancha.estado.nombre.lower()}.",
            )
            return redirect("dashboard")
        fecha = datetime.strptime(request.POST.get("fecha", ""), "%Y-%m-%d").date()
        hora_inicio = datetime.strptime(
            request.POST.get("hora_inicio", ""), "%H:%M"
        ).time()
        hora_fin = datetime.strptime(request.POST.get("hora_fin", ""), "%H:%M").time()
    except (Cancha.DoesNotExist, TypeError, ValueError):
        messages.error(request, "Completa correctamente la cancha, fecha y horario.")
        return redirect("dashboard")

    if fecha < timezone.localdate() or hora_fin <= hora_inicio:
        messages.error(request, "La fecha y el rango de horas no son válidos.")
        return redirect("dashboard")

    if hora_inicio.minute not in (0, 30) or hora_fin.minute not in (0, 30):
        messages.error(
            request, "Selecciona horarios en intervalos de 30 minutos (:00 o :30)."
        )
        return redirect("dashboard")

    cliente = request.user
    if _is_staff_role(request.user):
        cliente_id = request.POST.get("cliente_id")
        dni = request.POST.get("cliente_dni", "").strip()
        clientes = Usuario.objects.filter(rol__nombre="Cliente", activo=True)
        cliente = (
            clientes.filter(pk=cliente_id).first()
            if cliente_id
            else clientes.filter(dni=dni).first()
        )
        if not cliente:
            messages.error(request, "Selecciona un cliente válido para la reserva.")
            return redirect("dashboard")

    overlap = (
        Reserva.objects.filter(
            cancha=cancha,
            fecha=fecha,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio,
        )
        .exclude(estado__nombre__iexact="Cancelada")
        .exists()
    )
    if overlap:
        messages.error(
            request, "Ese horario ya está ocupado para la cancha seleccionada."
        )
        return redirect("dashboard")

    start = datetime.combine(fecha, hora_inicio)
    end = datetime.combine(fecha, hora_fin)
    duration = Decimal(str((end - start).total_seconds() / 3600)).quantize(
        Decimal("0.01")
    )
    if duration < Decimal("1.00") or duration % Decimal("0.50") != 0:
        messages.error(
            request,
            "La reserva debe durar al menos una hora y avanzar en bloques de 30 minutos.",
        )
        return redirect("dashboard")
    monto_total = (duration * cancha.precio_por_hora).quantize(Decimal("0.01"))

    if not _is_staff_role(request.user) and request.POST.get("add_to_cart") == "1":
        cart = request.session.get("reservation_cart", [])
        cart_overlap = any(
            str(cancha.pk) == str(item["cancha_id"])
            and fecha.isoformat() == item["fecha"]
            and hora_inicio.strftime("%H:%M") < item["hora_fin"]
            and hora_fin.strftime("%H:%M") > item["hora_inicio"]
            for item in cart
        )
        if cart_overlap:
            messages.error(request, "Ese horario ya está incluido en tu carrito.")
            return redirect("dashboard")
        cart.append(
            {
                "key": f'{cancha.pk}-{fecha.isoformat()}-{hora_inicio.strftime("%H%M")}',
                "cancha_id": cancha.pk,
                "cancha_nombre": cancha.nombre,
                "cancha_tipo": cancha.tipo,
                "fecha": fecha.isoformat(),
                "hora_inicio": hora_inicio.strftime("%H:%M"),
                "hora_fin": hora_fin.strftime("%H:%M"),
                "duracion": str(duration),
                "monto": str(monto_total),
                "observaciones": request.POST.get("observaciones", "").strip()[:1000],
            }
        )
        request.session["reservation_cart"] = cart
        request.session.modified = True
        messages.success(request, f"{cancha.nombre} fue agregada al carrito.")
        return redirect("dashboard")

    estado, _ = EstadoReserva.objects.get_or_create(nombre="Pendiente")
    reserva = Reserva.objects.create(
        cancha=cancha,
        cliente=cliente,
        estado=estado,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        duracion_horas=duration,
        monto_total=monto_total,
        observaciones=request.POST.get("observaciones", "").strip()[:1000],
    )
    _notify(
        cliente,
        reserva,
        f"Tu reserva #{reserva.pk} para {cancha.nombre} fue registrada.",
        "Reserva registrada",
    )

    if _is_staff_role(request.user) and request.POST.get("pagar_ahora") == "1":
        from pagos.models import Pago, MetodoPago, EstadoPago

        metodo = MetodoPago.objects.filter(
            pk=request.POST.get("metodo_pago_id"), activo=True
        ).first()
        if metodo:
            estado_pago, _ = EstadoPago.objects.get_or_create(nombre="Completado")
            Pago.objects.create(
                reserva=reserva,
                metodo_pago=metodo,
                estado_pago=estado_pago,
                monto=reserva.monto_total,
                codigo_operacion=request.POST.get("codigo_operacion", "").strip()[:100],
                observacion="Pago registrado al crear la reserva",
            )
            reserva.monto_pagado = reserva.monto_total
            reserva.estado, _ = EstadoReserva.objects.get_or_create(nombre="Confirmada")
            reserva.save(update_fields=["monto_pagado", "estado"])
            messages.success(
                request, f"Reserva #{reserva.pk} creada y pagada al momento."
            )
            return redirect("dashboard")
        messages.warning(
            request,
            f"Reserva #{reserva.pk} creada, pero selecciona un método para registrar el pago.",
        )
        return redirect("dashboard")
    messages.success(request, f"Reserva #{reserva.pk} creada correctamente.")
    return redirect("dashboard")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def cancel_reservation(request, reservation_id):
    from reservas.models import Reserva, EstadoReserva

    role = _role_name(request.user)
    query = Reserva.objects.select_related("estado", "cliente")
    reserva = (
        query.filter(pk=reservation_id).first()
        if _is_staff_role(request.user)
        else query.filter(pk=reservation_id, cliente=request.user).first()
    )
    if not reserva or (role != "Cliente" and not _is_staff_role(request.user)):
        messages.error(request, "No tienes permiso para cancelar esta reserva.")
        return _reservation_redirect(request)
    if reserva.monto_pagado > 0:
        messages.error(
            request, "No se puede cancelar una reserva que ya tiene un pago registrado."
        )
        return _reservation_redirect(request)
    start = timezone.make_aware(datetime.combine(reserva.fecha, reserva.hora_inicio))
    if start <= timezone.now():
        messages.error(request, "No se puede cancelar una reserva que ya comenzó.")
        return _reservation_redirect(request)
    if reserva.estado.nombre.lower() in ("cancelada", "finalizada"):
        messages.error(request, "La reserva ya está cerrada.")
        return _reservation_redirect(request)
    reserva.estado, _ = EstadoReserva.objects.get_or_create(nombre="Cancelada")
    reserva.save(update_fields=["estado"])
    _notify(
        reserva.cliente,
        reserva,
        f"Tu reserva #{reserva.pk} fue cancelada.",
        "Reserva cancelada",
    )
    messages.success(request, f"Reserva #{reserva.pk} cancelada correctamente.")
    return _reservation_redirect(request)


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def update_attendance(request, reservation_id):
    from reservas.models import Reserva, EstadoReserva

    if not _is_staff_role(request.user):
        messages.error(request, "No tienes permiso para controlar asistencias.")
        return _reservation_redirect(request)
    reserva = Reserva.objects.filter(pk=reservation_id).first()
    if not reserva:
        messages.error(request, "La reserva no existe.")
        return _reservation_redirect(request)
    action = request.POST.get("action")
    states = {"arrived": "En curso", "completed": "Finalizada", "no_show": "No asistió"}
    if action not in states:
        messages.error(request, "Acción de asistencia inválida.")
        return _reservation_redirect(request)
    reserva.estado, _ = EstadoReserva.objects.get_or_create(nombre=states[action])
    if action == "arrived":
        reserva.hora_llegada = timezone.localtime().time().replace(microsecond=0)
        reserva.save(update_fields=["estado", "hora_llegada"])
    else:
        reserva.save(update_fields=["estado"])
    _notify(
        reserva.cliente,
        reserva,
        f"El estado de tu reserva #{reserva.pk} cambió a {states[action]}.",
        "Estado de asistencia",
    )
    messages.success(request, f"Reserva #{reserva.pk}: {states[action]}.")
    return _reservation_redirect(request)


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def delete_reservation(request, reservation_id):
    """Permite a recepción y administración eliminar una reserva."""
    from reservas.models import Reserva

    if not _is_staff_role(request.user):
        messages.error(request, "No tienes permiso para eliminar reservas.")
        return redirect("dashboard")
    reserva = Reserva.objects.filter(pk=reservation_id).first()
    if not reserva:
        messages.error(request, "La reserva ya no existe.")
    elif reserva.monto_pagado > 0:
        messages.error(
            request, "No se puede eliminar una reserva que ya tiene un pago registrado."
        )
    else:
        code = reserva.pk
        reserva.delete()
        messages.success(request, f"Reserva #{code} eliminada.")
    return redirect("dashboard")
