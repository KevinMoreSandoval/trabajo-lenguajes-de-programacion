from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from authentication.models import Rol, Usuario
from canchas.models import Cancha, HorarioBloqueado
from pagos.models import EstadoPago, Pago

from .forms import BuscarClienteForm, DURACIONES, HORA_APERTURA, HORA_CIERRE, INTERVALO_MINUTOS, ReservaForm, ReservaMultipleForm, ReservaRecepcionForm, generar_horas_predeterminadas
from .models import EstadoReserva, Reserva, ReservaGrupo

logger = logging.getLogger(__name__)


def operador_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_operador', False):
            messages.error(request, 'Solo administradores o recepcionistas pueden realizar esta accion.')
            return redirect('reservas:mis_reservas')
        return view_func(request, *args, **kwargs)
    return wrapper


def cliente_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_cliente', False):
            messages.error(request, 'Esta accion esta disponible solo para clientes.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def existe_cruce(cancha, fecha, hora_inicio, hora_fin, reserva_id=None):
    reservas = Reserva.objects.filter(
        cancha=cancha,
        fecha=fecha,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    ).exclude(estado__nombre='Cancelada')
    if reserva_id:
        reservas = reservas.exclude(pk=reserva_id)

    bloqueos = HorarioBloqueado.objects.filter(
        cancha=cancha,
        fecha=fecha,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    )

    return reservas.exists() or bloqueos.exists()


def rango_horario_valido(hora_inicio, hora_fin):
    inicio_dt = datetime.combine(timezone.localdate(), hora_inicio)
    fin_dt = datetime.combine(timezone.localdate(), hora_fin)
    duracion_minutos = int((fin_dt - inicio_dt).total_seconds() // 60)
    return (
        hora_inicio < hora_fin
        and hora_inicio >= HORA_APERTURA
        and hora_fin <= HORA_CIERRE
        and hora_inicio.minute in (0, 30)
        and hora_fin.minute in (0, 30)
        and duracion_minutos >= 60
        and duracion_minutos % INTERVALO_MINUTOS == 0
    )


def calcular_item_reserva(item):
    cancha = Cancha.objects.select_related('estado').get(pk=item['cancha_id'])
    fecha = datetime.strptime(item['fecha'], '%Y-%m-%d').date()
    hora_inicio = datetime.strptime(item['hora_inicio'], '%H:%M').time()
    hora_fin = datetime.strptime(item['hora_fin'], '%H:%M').time()

    if fecha < timezone.localdate():
        raise ValueError('No puedes reservar fechas pasadas.')
    if not rango_horario_valido(hora_inicio, hora_fin):
        raise ValueError('El horario debe estar entre 08:00 y 23:00, minimo 1 hora y en rangos de 30 minutos.')

    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.combine(fecha, hora_fin)
    duracion_minutos = int((fin_dt - inicio_dt).total_seconds() // 60)
    subtotal = cancha.precio_por_hora * (Decimal(duracion_minutos) / Decimal('60'))

    return {
        'cancha': cancha,
        'fecha': fecha,
        'hora_inicio': hora_inicio,
        'hora_fin': hora_fin,
        'duracion_minutos': duracion_minutos,
        'duracion_horas': Decimal(duracion_minutos) / Decimal('60'),
        'precio_por_hora': cancha.precio_por_hora,
        'subtotal': subtotal,
    }


def validar_conflictos_items(items_calculados):
    for index, item in enumerate(items_calculados):
        if existe_cruce(item['cancha'], item['fecha'], item['hora_inicio'], item['hora_fin']):
            raise ValueError(
                f"{item['cancha'].nombre} ya esta ocupada de "
                f"{item['hora_inicio'].strftime('%H:%M')} a {item['hora_fin'].strftime('%H:%M')}."
            )

        for otro in items_calculados[index + 1:]:
            mismo_recurso = item['cancha'].id == otro['cancha'].id and item['fecha'] == otro['fecha']
            solapa = item['hora_inicio'] < otro['hora_fin'] and item['hora_fin'] > otro['hora_inicio']
            if mismo_recurso and solapa:
                raise ValueError(
                    f"Hay dos selecciones cruzadas para {item['cancha'].nombre}: "
                    f"{item['hora_inicio'].strftime('%H:%M')} - {item['hora_fin'].strftime('%H:%M')}."
                )


def cambiar_estado_reserva(reserva, estado_nombre):
    estado, _ = EstadoReserva.objects.get_or_create(nombre=estado_nombre)
    reserva.estado = estado
    reserva.save(update_fields=['estado'])


def crear_pago_reserva(reserva, metodo_pago, monto, observacion=''):
    estado_pago, _ = EstadoPago.objects.get_or_create(nombre='Pagado')
    Pago.objects.create(
        reserva=reserva,
        metodo_pago=metodo_pago,
        estado_pago=estado_pago,
        monto=monto,
        observacion=observacion,
    )
    reserva.monto_pagado = monto
    reserva.save(update_fields=['monto_pagado'])


def construir_horarios(cancha, fecha):
    horarios = []
    cierre = datetime.combine(fecha, HORA_CIERRE)

    for hora_predeterminada in generar_horas_predeterminadas():
        inicio = datetime.combine(fecha, hora_predeterminada)
        hora_inicio = inicio.time()
        duraciones_disponibles = []

        for duracion, etiqueta in DURACIONES:
            fin = inicio + timedelta(minutes=int(duracion * 60))
            if fin > cierre:
                continue
            if not existe_cruce(cancha, fecha, hora_inicio, fin.time()):
                duraciones_disponibles.append({
                    'valor': f'{duracion:.2f}',
                    'etiqueta': etiqueta,
                    'hora_fin': fin.time(),
                    'precio': cancha.precio_por_hora * duracion,
                })

        horarios.append({
            'hora_inicio': hora_inicio,
            'ocupado': not duraciones_disponibles,
            'duraciones': duraciones_disponibles,
        })

    return horarios


@cliente_required
def carrito_reservas(request):
    canchas = Cancha.objects.select_related('estado').filter(estado__nombre__iexact='Disponible').order_by('nombre')
    if not canchas.exists():
        canchas = Cancha.objects.select_related('estado').order_by('nombre')

    context = {
        'canchas': canchas,
        'fecha_minima': timezone.localdate(),
        'horas_predeterminadas': generar_horas_predeterminadas(),
    }

    if request.method == 'POST':
        form = ReservaMultipleForm(request.POST)
        if form.is_valid():
            try:
                items = json.loads(form.cleaned_data['items_json'])
                if not isinstance(items, list) or not items:
                    raise ValueError('Agrega al menos una reserva al carrito.')

                items_calculados = [calcular_item_reserva(item) for item in items]

                with transaction.atomic():
                    validar_conflictos_items(items_calculados)
                    estado, _ = EstadoReserva.objects.get_or_create(nombre='Pendiente')
                    grupo = ReservaGrupo.objects.create(cliente=request.user, estado='pendiente')
                    total_general = Decimal('0.00')

                    for item in items_calculados:
                        Reserva.objects.create(
                            grupo=grupo,
                            cancha=item['cancha'],
                            cliente=request.user,
                            estado=estado,
                            fecha=item['fecha'],
                            hora_inicio=item['hora_inicio'],
                            hora_fin=item['hora_fin'],
                            duracion_horas=item['duracion_horas'],
                            duracion_minutos=item['duracion_minutos'],
                            precio_por_hora=item['precio_por_hora'],
                            subtotal=item['subtotal'],
                            monto_total=item['subtotal'],
                        )
                        total_general += item['subtotal']

                    grupo.total_general = total_general
                    grupo.save(update_fields=['total_general'])

                messages.success(request, f'Reservas agregadas correctamente. Total: S/ {total_general}.')
                return redirect('reservas:mis_reservas')
            except (ValueError, KeyError, Cancha.DoesNotExist, json.JSONDecodeError) as exc:
                messages.error(request, str(exc) or 'No se pudo procesar el carrito.')
            except DatabaseError:
                logger.exception('Error creando carrito de reservas para cliente %s', request.user.id)
                messages.error(request, 'No se pudo confirmar el carrito. Intentalo nuevamente.')

    return render(request, 'reservas/carrito.html', context)

def mis_reservas(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Inicia sesion para ver tus reservas.')
        return redirect('signin')

    try:
        reservas = Reserva.objects.select_related('cancha', 'cliente', 'estado')
        es_operador = getattr(request.user, 'es_operador', False)
        if not es_operador:
            reservas = reservas.filter(cliente=request.user)
        reservas = reservas.order_by('-fecha', '-hora_inicio')
    except DatabaseError:
        logger.exception('Error listando reservas')
        messages.error(request, 'No se pudieron cargar las reservas.')
        reservas = []
        es_operador = getattr(request.user, 'es_operador', False)

    return render(
        request,
        'reservas/mis_reservas.html',
        {'reservas': reservas, 'es_operador': es_operador},
    )


@operador_required
def recepcion_buscar_cliente(request):
    if request.method == 'POST':
        form = BuscarClienteForm(request.POST)
        if form.is_valid():
            dni = form.cleaned_data['dni']
            try:
                cliente = Usuario.objects.filter(rol__nombre=Rol.CLIENTE, dni=dni).first()
            except DatabaseError:
                logger.exception('Error buscando cliente con DNI %s', dni)
                messages.error(request, 'No se pudo buscar el cliente. Intentalo nuevamente.')
                return redirect('reservas:recepcion_buscar_cliente')
            if cliente:
                return redirect(f"{reverse('reservas:recepcion_crear')}?cliente={cliente.id}")
            messages.info(request, 'Cliente no encontrado. Registralo antes de crear la reserva.')
            return redirect(f"{reverse('usuarios:crear_cliente')}?dni={dni}")
    else:
        form = BuscarClienteForm()

    return render(request, 'reservas/recepcion_buscar_cliente.html', {'form': form})


@operador_required
def recepcion_crear_reserva(request):
    cliente_id = request.GET.get('cliente') or request.POST.get('cliente')
    cliente = get_object_or_404(Usuario.objects.filter(rol__nombre=Rol.CLIENTE), pk=cliente_id)

    if request.method == 'POST':
        form = ReservaRecepcionForm(request.POST)
        if form.is_valid():
            cancha = form.cleaned_data['cancha']
            fecha = form.cleaned_data['fecha']
            hora_inicio = form.cleaned_data['hora_inicio']
            hora_fin = form.cleaned_data['hora_fin']
            duracion_horas = form.cleaned_data['duracion_horas']

            if existe_cruce(cancha, fecha, hora_inicio, hora_fin):
                messages.error(request, 'Ese horario no esta disponible para la cancha seleccionada.')
            else:
                try:
                    with transaction.atomic():
                        estado, _ = EstadoReserva.objects.get_or_create(nombre='Confirmada')
                        monto_total = cancha.precio_por_hora * duracion_horas
                        reserva = Reserva.objects.create(
                            cancha=cancha,
                            cliente=cliente,
                            estado=estado,
                            fecha=fecha,
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            duracion_horas=duracion_horas,
                            monto_total=monto_total,
                            monto_pagado=monto_total,
                            observaciones=form.cleaned_data['observaciones'],
                        )
                        crear_pago_reserva(
                            reserva,
                            form.cleaned_data['metodo_pago'],
                            monto_total,
                            form.cleaned_data['observaciones'],
                        )
                    messages.success(request, 'Reserva presencial creada correctamente.')
                    return redirect('reservas:mis_reservas')
                except DatabaseError:
                    logger.exception('Error creando reserva presencial para cliente %s', cliente.id)
                    messages.error(request, 'No se pudo crear la reserva. Intentalo nuevamente.')
    else:
        form = ReservaRecepcionForm()

    return render(
        request,
        'reservas/recepcion_form.html',
        {'form': form, 'cliente': cliente},
    )


@cliente_required
def crear_reserva(request, cancha_id):
    cancha = get_object_or_404(Cancha.objects.select_related('estado'), pk=cancha_id)
    fecha_seleccionada = timezone.localdate()

    if request.method == 'POST':
        form = ReservaForm(request.POST, es_operador=False)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            hora_inicio = form.cleaned_data['hora_inicio']
            hora_fin = form.cleaned_data['hora_fin']
            duracion_horas = form.cleaned_data['duracion_horas']

            if existe_cruce(cancha, fecha, hora_inicio, hora_fin):
                messages.error(request, 'Ese horario no esta disponible para la cancha seleccionada.')
            else:
                try:
                    with transaction.atomic():
                        estado, _ = EstadoReserva.objects.get_or_create(nombre='Pendiente')
                        monto_total = cancha.precio_por_hora * duracion_horas
                        reserva = Reserva.objects.create(
                            cancha=cancha,
                            cliente=request.user,
                            estado=estado,
                            fecha=fecha,
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            duracion_horas=duracion_horas,
                            monto_total=monto_total,
                            observaciones=form.cleaned_data['observaciones'],
                        )
                    return redirect('pagos:pagar_reserva', reserva_id=reserva.id)
                except DatabaseError:
                    logger.exception('Error creando reserva para cliente %s', request.user.id)
                    messages.error(request, 'No se pudo crear la reserva. Intentalo nuevamente.')
    else:
        fecha_query = request.GET.get('fecha')
        if fecha_query:
            try:
                fecha_seleccionada = datetime.strptime(fecha_query, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Fecha invalida.')

    context = {
        'cancha': cancha,
        'fecha_seleccionada': fecha_seleccionada,
        'fecha_minima': timezone.localdate(),
        'horarios': [],
        'hora_apertura': HORA_APERTURA,
        'hora_cierre': HORA_CIERRE,
        'intervalo_minutos': INTERVALO_MINUTOS,
    }

    try:
        context['horarios'] = construir_horarios(cancha, fecha_seleccionada)
    except DatabaseError:
        logger.exception('Error construyendo horarios para cancha %s', cancha_id)
        messages.error(request, 'No se pudieron cargar los horarios disponibles.')

    return render(request, 'reservas/crear.html', context)


@login_required(login_url='signin')
def reserva_confirmada(request, reserva_id):
    reserva = get_object_or_404(
        Reserva.objects.select_related('cancha', 'estado', 'cliente'),
        pk=reserva_id,
        cliente=request.user,
    )
    return render(request, 'reservas/confirmada.html', {'reserva': reserva})


@require_POST
@login_required(login_url='signin')
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva.objects.select_related('cliente'), pk=reserva_id)
    if not getattr(request.user, 'es_operador', False) and reserva.cliente != request.user:
        messages.error(request, 'No tienes permiso para cancelar esta reserva.')
        return redirect('reservas:mis_reservas')

    try:
        cambiar_estado_reserva(reserva, 'Cancelada')
        messages.success(request, 'Reserva cancelada correctamente.')
    except DatabaseError:
        logger.exception('Error cancelando reserva %s', reserva_id)
        messages.error(request, 'No se pudo cancelar la reserva.')
    return redirect('reservas:mis_reservas')


@require_POST
@operador_required
def confirmar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    try:
        cambiar_estado_reserva(reserva, 'Confirmada')
        messages.success(request, 'Reserva confirmada correctamente.')
    except DatabaseError:
        logger.exception('Error confirmando reserva %s', reserva_id)
        messages.error(request, 'No se pudo confirmar la reserva.')
    return redirect('reservas:mis_reservas')


@require_POST
@operador_required
def finalizar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    try:
        cambiar_estado_reserva(reserva, 'Finalizada')
        messages.success(request, 'Reserva finalizada correctamente.')
    except DatabaseError:
        logger.exception('Error finalizando reserva %s', reserva_id)
        messages.error(request, 'No se pudo finalizar la reserva.')
    return redirect('reservas:mis_reservas')
