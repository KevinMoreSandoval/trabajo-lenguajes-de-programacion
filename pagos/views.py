from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404, redirect, render
import logging

from reservas.models import Reserva
from reservas.models import EstadoReserva

from .forms import PagoForm
from .models import EstadoPago, Pago

logger = logging.getLogger(__name__)


def cliente_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_cliente', False):
            messages.error(request, 'El pago de reservas esta disponible solo para clientes.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@cliente_required
def pagar_reserva(request, reserva_id):
    reserva = get_object_or_404(
        Reserva.objects.select_related('cancha', 'cliente', 'estado'),
        pk=reserva_id,
        cliente=request.user,
    )

    saldo = reserva.monto_total - reserva.monto_pagado

    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data['monto']
            if monto > saldo:
                messages.error(request, 'El monto no puede ser mayor al saldo pendiente.')
            else:
                try:
                    with transaction.atomic():
                        estado_pago, _ = EstadoPago.objects.get_or_create(nombre='Pagado')
                        Pago.objects.create(
                            reserva=reserva,
                            metodo_pago=form.cleaned_data['metodo_pago'],
                            estado_pago=estado_pago,
                            monto=monto,
                            referencia=form.cleaned_data['referencia'],
                            codigo_operacion=form.cleaned_data['codigo_operacion'],
                            observacion=form.cleaned_data['observacion'],
                        )
                        reserva.monto_pagado += monto
                        update_fields = ['monto_pagado']
                        if reserva.monto_pagado >= reserva.monto_total:
                            estado_reserva, _ = EstadoReserva.objects.get_or_create(nombre='Pagada')
                            reserva.estado = estado_reserva
                            update_fields.append('estado')
                        reserva.save(update_fields=update_fields)
                    messages.success(request, 'Reserva confirmada correctamente.')
                    return redirect('reservas:confirmada', reserva_id=reserva.id)
                except DatabaseError:
                    logger.exception('Error registrando pago de reserva %s', reserva_id)
                    messages.error(request, 'No se pudo registrar el pago. Intentalo nuevamente.')
    else:
        form = PagoForm(initial={'monto': saldo})

    context = {
        'reserva': reserva,
        'saldo': saldo,
        'form': form,
    }

    return render(request, 'pagos/pagar.html', context)


@cliente_required
def cancelar_pago(request, reserva_id):
    reserva = get_object_or_404(
        Reserva.objects.select_related('cancha', 'cliente', 'estado'),
        pk=reserva_id,
        cliente=request.user,
    )

    if reserva.estado.nombre == 'Pendiente' and reserva.monto_pagado == 0:
        try:
            with transaction.atomic():
                estado_cancelada, _ = EstadoReserva.objects.get_or_create(nombre='Cancelada')
                reserva.estado = estado_cancelada
                reserva.save(update_fields=['estado'])
            messages.info(request, 'Reserva pendiente anulada. El horario quedo disponible.')
        except DatabaseError:
            logger.exception('Error anulando pago/reserva pendiente %s', reserva_id)
            messages.error(request, 'No se pudo anular la reserva pendiente.')

    return redirect('canchas:lista')
