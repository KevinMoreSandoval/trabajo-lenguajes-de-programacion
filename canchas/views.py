"""Casos de uso HTTP del dominio de canchas."""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from authentication.views import _is_admin_role
from .models import Cancha, CanchaFutbol, EstadoCancha, Horario


@login_required(login_url="signin")
@require_http_methods(["GET"])
def court_availability(request):
    from reservas.models import Reserva

    try:
        selected_date = datetime.strptime(
            request.GET.get("fecha", ""), "%Y-%m-%d"
        ).date()
    except ValueError:
        return JsonResponse({"canchas": []}, status=400)
    result = []
    courts = Cancha.objects.select_related("estado").exclude(estado__nombre="Inactiva")
    for court in courts:
        reservations = list(
            Reserva.objects.filter(cancha=court, fecha=selected_date)
            .exclude(estado__nombre__iexact="Cancelada")
            .values_list("hora_inicio", "hora_fin")
        )
        slots = []
        current = datetime.combine(
            selected_date, datetime.strptime("08:00", "%H:%M").time()
        )
        limit = datetime.combine(
            selected_date, datetime.strptime("23:00", "%H:%M").time()
        )
        while current <= limit:
            end = current + timedelta(minutes=30)
            occupied = any(
                current.time() < finish and end.time() > start
                for start, finish in reservations
            )
            slots.append(
                {
                    "hora": current.strftime("%H:%M"),
                    "disponible": court.estado.nombre == "Disponible" and not occupied,
                }
            )
            current = end
        result.append(
            {
                "nombre": court.nombre,
                "tipo": court.tipo,
                "estado": court.estado.nombre,
                "imagen": court.imagen_src,
                "slots": slots,
            }
        )
    return JsonResponse({"fecha": selected_date.isoformat(), "canchas": result})


def _admin_page():
    return redirect("staff_page", section="administracion")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def create_court(request):
    if not _is_admin_role(request.user):
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect("dashboard")
    try:
        estado, _ = EstadoCancha.objects.get_or_create(nombre="Disponible")
        tipo = request.POST["tipo"].strip()
        cancha = Cancha.objects.create(
            estado=estado,
            nombre=request.POST["nombre"].strip(),
            tipo=tipo,
            capacidad=int(request.POST["capacidad"]),
            precio_por_hora=Decimal(request.POST["precio"]),
            ubicacion=request.POST["ubicacion"].strip(),
            descripcion=request.POST.get("descripcion", "").strip(),
            imagen_url=request.POST.get("imagen_url", "").strip()
            or "/static/img/courts/futbol-5.jpeg",
            imagen=request.FILES.get("imagen"),
            techada=request.POST.get("techada") == "on",
            iluminacion=request.POST.get("iluminacion") == "on",
            banos=request.POST.get("banos") == "on",
        )
        if "fútbol" in tipo.lower() or "futbol" in tipo.lower():
            CanchaFutbol.objects.create(
                cancha=cancha,
                tipo_cesped=request.POST.get("tipo_cesped", "").strip(),
                arcos_profesional=request.POST.get("arcos_profesional") == "on",
            )
        messages.success(request, "Cancha creada correctamente.")
    except (KeyError, ValueError, InvalidOperation):
        messages.error(request, "Completa correctamente los datos de la cancha.")
    return _admin_page()


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def update_court_status(request, court_id):
    if not _is_admin_role(request.user):
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect("dashboard")
    allowed = {"Disponible", "Mantenimiento", "Inactiva"}
    status = request.POST.get("estado")
    cancha = Cancha.objects.filter(pk=court_id).first()
    if not cancha or status not in allowed:
        messages.error(request, "Cancha o estado no válido.")
    else:
        cancha.estado, _ = EstadoCancha.objects.get_or_create(nombre=status)
        cancha.save(update_fields=["estado"])
        messages.success(request, f"{cancha.nombre}: estado actualizado a {status}.")
    return _admin_page()


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def create_schedule(request):
    if not _is_admin_role(request.user):
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect("dashboard")
    try:
        cancha = Cancha.objects.get(pk=request.POST.get("cancha_id"))
        start = datetime.strptime(request.POST["hora_inicio"], "%H:%M").time()
        end = datetime.strptime(request.POST["hora_fin"], "%H:%M").time()
        if end <= start or start.minute not in (0, 30) or end.minute not in (0, 30):
            raise ValueError
        Horario.objects.get_or_create(cancha=cancha, hora_inicio=start, hora_fin=end)
        messages.success(request, "Horario configurado correctamente.")
    except (Cancha.DoesNotExist, KeyError, ValueError):
        messages.error(request, "El horario seleccionado no es válido.")
    return _admin_page()
