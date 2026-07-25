"""Vistas de exportación de reportes."""

from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from authentication.views import _is_admin_role
from reservas.models import Reserva
from .pdf import _reservations_report_pdf


@login_required(login_url="signin")
@require_http_methods(["GET"])
def reservations_pdf(request):
    """Exporta reservas y cobros del periodo solicitado en formato PDF."""
    if not _is_admin_role(request.user):
        return HttpResponse("Acceso denegado", status=403)

    mode = request.GET.get("periodo", "dia")
    today = timezone.localdate()
    try:
        if mode == "fecha":
            start = end = datetime.strptime(request.GET["fecha"], "%Y-%m-%d").date()
        elif mode == "rango":
            start = datetime.strptime(request.GET["desde"], "%Y-%m-%d").date()
            end = datetime.strptime(request.GET["hasta"], "%Y-%m-%d").date()
            if end < start:
                raise ValueError
        else:
            start = end = today
    except (KeyError, ValueError):
        messages.error(request, "Selecciona un periodo válido para el reporte.")
        return redirect("staff_page", section="administracion")

    reservations = (
        Reserva.objects.select_related("cliente", "cancha", "estado")
        .filter(fecha__range=(start, end))
        .order_by("fecha", "hora_inicio")
    )
    total = sum((item.monto_pagado for item in reservations), Decimal("0.00"))
    response = HttpResponse(
        _reservations_report_pdf(reservations, start, end, total),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_reservas_{start}_{end}.pdf"'
    )
    return response
