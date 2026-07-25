import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from authentication.models import Usuario
from pagos.models import MetodoPago, Pago
from reservas.models import EstadoReserva, Reserva
from services.analytics import (
    get_horas_vendidas_por_dia,
    get_ingresos_por_dia,
    get_kpis,
    get_ocupacion_por_cancha,
    get_reservas_por_cancha,
    get_top_canchas,
)

from .forms import CanchaForm, HorarioBloqueadoForm
from .models import Cancha, HorarioBloqueado, Regla

logger = logging.getLogger(__name__)


def admin_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_admin', False):
            messages.error(request, 'Solo el administrador puede gestionar canchas.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def operador_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_operador', False):
            messages.error(request, 'Solo administradores o recepcionistas pueden gestionar horarios.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def dashboard(request):
    usuario_autenticado = request.user.is_authenticated
    rol_usuario = request.user.rol.nombre if usuario_autenticado and request.user.rol else 'Visitante'
    es_admin = rol_usuario == 'Admin'
    es_recepcionista = rol_usuario == 'Recepcionista'
    es_operador = es_admin or es_recepcionista
    es_cliente = rol_usuario == 'Cliente'

    if not usuario_autenticado:
        return redirect('signin')

    if es_cliente:
        return redirect('canchas:lista')

    if es_operador:
        try:
            context = {
                'canchas': Cancha.objects.order_by('nombre'),
                'usuarios': Usuario.objects.select_related('rol').order_by('first_name', 'last_name', 'email'),
                'estados': EstadoReserva.objects.order_by('nombre'),
                'fecha_hoy': timezone.localdate().isoformat(),
            }
        except DatabaseError:
            logger.exception('Error cargando filtros del dashboard BI')
            messages.error(request, 'No se pudieron cargar los filtros del dashboard.')
            context = {'canchas': [], 'usuarios': [], 'estados': [], 'fecha_hoy': timezone.localdate().isoformat()}
        return render(request, 'dashboard_bi.html', context)

    try:
        canchas_count = Cancha.objects.count()
        reglas_count = Regla.objects.count()
        recent_canchas = Cancha.objects.select_related('estado').order_by('-fecha_creacion')[:5]
        canchas_disponibles = Cancha.objects.select_related('estado').filter(estado__nombre__iexact='Disponible')
        canchas_disponibles_count = canchas_disponibles.count()
        if not canchas_disponibles_count:
            canchas_disponibles = Cancha.objects.select_related('estado').order_by('-fecha_creacion')
        metodos_pago = MetodoPago.objects.select_related('tipo').filter(activo=True).order_by('nombre')
        fecha_filtro = request.GET.get('fecha') or timezone.localdate().isoformat()
        reservas_dia = (
            Reserva.objects
            .select_related('cancha', 'cliente', 'estado')
            .filter(fecha=fecha_filtro)
            .order_by('hora_inicio')
        )
        canchas_ocupadas_count = (
            reservas_dia
            .exclude(estado__nombre='Cancelada')
            .values('cancha')
            .distinct()
            .count()
        )
    except DatabaseError:
        logger.exception('Error cargando dashboard')
        messages.error(request, 'No se pudo cargar el dashboard completo.')
        canchas_count = reglas_count = canchas_disponibles_count = canchas_ocupadas_count = 0
        recent_canchas = canchas_disponibles = metodos_pago = reservas_dia = []
        fecha_filtro = request.GET.get('fecha') or timezone.localdate().isoformat()

    if es_operador:
        try:
            reservas_count = Reserva.objects.count()
            pagos_count = Pago.objects.count()
            usuarios_count = Usuario.objects.count() if es_admin else 0

            recent_reservas = (
                Reserva.objects
                .select_related('cancha', 'cliente', 'estado')
                .order_by('-fecha_creacion')[:5]
            )
            recent_pagos = (
                Pago.objects
                .select_related('reserva', 'metodo_pago', 'estado_pago')
                .order_by('-fecha_pago')[:5]
            )
            recent_usuarios = Usuario.objects.select_related('rol').order_by('-fecha_creacion')[:5] if es_admin else []
        except DatabaseError:
            logger.exception('Error cargando resumen de operador')
            messages.error(request, 'No se pudo cargar el resumen de operaciones.')
            reservas_count = pagos_count = usuarios_count = 0
            recent_reservas = recent_pagos = recent_usuarios = []
    elif usuario_autenticado:
        reservas_count = Reserva.objects.filter(cliente=request.user).count()
        pagos_count = Pago.objects.filter(reserva__cliente=request.user).count()
        usuarios_count = 0

        recent_reservas = (
            Reserva.objects
            .select_related('cancha', 'cliente', 'estado')
            .filter(cliente=request.user)
            .order_by('-fecha_creacion')[:5]
        )
        recent_pagos = (
            Pago.objects
            .select_related('reserva', 'metodo_pago', 'estado_pago')
            .filter(reserva__cliente=request.user)
            .order_by('-fecha_pago')[:5]
        )
        recent_usuarios = []
    else:
        reservas_count = Reserva.objects.count()
        pagos_count = Pago.objects.count()
        usuarios_count = 0

        recent_reservas = (
            Reserva.objects
            .select_related('cancha', 'cliente', 'estado')
            .order_by('-fecha_creacion')[:5]
        )
        recent_pagos = (
            Pago.objects
            .select_related('reserva', 'metodo_pago', 'estado_pago')
            .order_by('-fecha_pago')[:5]
        )
        recent_usuarios = []

    context = {
        'rol_usuario': rol_usuario,
        'usuario_autenticado': usuario_autenticado,
        'es_admin': es_admin,
        'es_recepcionista': es_recepcionista,
        'es_operador': es_operador,
        'es_cliente': es_cliente,
        'canchas_count': canchas_count,
        'canchas_disponibles_count': canchas_disponibles_count,
        'reglas_count': reglas_count,
        'reservas_count': reservas_count,
        'pagos_count': pagos_count,
        'usuarios_count': usuarios_count,
        'recent_canchas': recent_canchas,
        'canchas_disponibles': canchas_disponibles[:4],
        'recent_reservas': recent_reservas,
        'recent_pagos': recent_pagos,
        'recent_usuarios': recent_usuarios,
        'metodos_pago': metodos_pago,
        'fecha_filtro': fecha_filtro,
        'reservas_dia': reservas_dia,
        'canchas_ocupadas_count': canchas_ocupadas_count,
    }

    return render(request, 'dashboard.html', context)


@operador_required
def api_dashboard_kpis(request):
    try:
        return JsonResponse(get_kpis(request.GET))
    except DatabaseError:
        logger.exception('Error calculando KPIs del dashboard')
        return JsonResponse({'error': 'No se pudieron calcular los indicadores.'}, status=500)


@operador_required
def api_dashboard_ingresos(request):
    try:
        return JsonResponse({
            'ingresos_por_dia': get_ingresos_por_dia(request.GET),
            'horas_por_dia': get_horas_vendidas_por_dia(request.GET),
            'top_canchas': get_top_canchas(request.GET, limit=8),
        })
    except DatabaseError:
        logger.exception('Error calculando ingresos del dashboard')
        return JsonResponse({'error': 'No se pudieron calcular los ingresos.'}, status=500)


@operador_required
def api_dashboard_ocupacion(request):
    try:
        return JsonResponse({'ocupacion': get_ocupacion_por_cancha(request.GET)})
    except DatabaseError:
        logger.exception('Error calculando ocupacion del dashboard')
        return JsonResponse({'error': 'No se pudo calcular la ocupacion.'}, status=500)


@operador_required
def api_dashboard_reservas(request):
    try:
        return JsonResponse({'reservas_por_cancha': get_reservas_por_cancha(request.GET)})
    except DatabaseError:
        logger.exception('Error calculando reservas del dashboard')
        return JsonResponse({'error': 'No se pudieron calcular las reservas.'}, status=500)


def lista_canchas(request):
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', '')
    try:
        canchas = (
            Cancha.objects
            .select_related('estado')
            .prefetch_related('reglas')
            .order_by('nombre')
        )
        if tipo:
            canchas = canchas.filter(tipo=tipo)
        if estado:
            canchas = canchas.filter(estado_id=estado)

        tipos = Cancha.objects.order_by('tipo').values_list('tipo', flat=True).distinct()
        estados = Cancha._meta.get_field('estado').remote_field.model.objects.order_by('nombre')
    except DatabaseError:
        logger.exception('Error listando canchas')
        messages.error(request, 'No se pudieron cargar las canchas.')
        canchas = tipos = estados = []

    return render(
        request,
        'canchas/lista.html',
        {'canchas': canchas, 'tipos': tipos, 'estados': estados, 'tipo_actual': tipo, 'estado_actual': estado},
    )


@admin_required
def crear_cancha(request):
    if request.method == 'POST':
        form = CanchaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, 'Cancha creada correctamente.')
                return redirect('canchas:lista')
            except DatabaseError:
                logger.exception('Error creando cancha')
                messages.error(request, 'No se pudo crear la cancha. Revisa los datos e intentalo nuevamente.')
    else:
        form = CanchaForm()

    return render(
        request,
        'canchas/form.html',
        {'form': form, 'titulo': 'Crear cancha', 'accion': 'Crear'},
    )


@admin_required
def editar_cancha(request, cancha_id):
    cancha = get_object_or_404(Cancha.objects.prefetch_related('reglas'), pk=cancha_id)

    if request.method == 'POST':
        form = CanchaForm(request.POST, instance=cancha)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, 'Cancha actualizada correctamente.')
                return redirect('canchas:detalle', cancha_id=cancha.id)
            except DatabaseError:
                logger.exception('Error editando cancha %s', cancha_id)
                messages.error(request, 'No se pudo actualizar la cancha.')
    else:
        form = CanchaForm(instance=cancha)

    return render(
        request,
        'canchas/form.html',
        {'form': form, 'titulo': 'Editar cancha', 'accion': 'Guardar'},
    )


@admin_required
def eliminar_cancha(request, cancha_id):
    cancha = get_object_or_404(Cancha, pk=cancha_id)

    if request.method == 'POST':
        try:
            cancha.delete()
            messages.success(request, 'Cancha eliminada correctamente.')
            return redirect('canchas:lista')
        except DatabaseError:
            logger.exception('Error eliminando cancha %s', cancha_id)
            messages.error(request, 'No se pudo eliminar la cancha porque puede tener reservas asociadas.')

    return render(request, 'canchas/confirm_delete.html', {'cancha': cancha})


@operador_required
def gestionar_horarios(request, cancha_id):
    cancha = get_object_or_404(Cancha.objects.select_related('estado'), pk=cancha_id)

    if request.method == 'POST':
        form = HorarioBloqueadoForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            hora_inicio = form.cleaned_data['hora_inicio']
            hora_fin = form.cleaned_data['hora_fin']
            reservas_cruzadas = Reserva.objects.filter(
                cancha=cancha,
                fecha=fecha,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            ).exclude(estado__nombre='Cancelada')
            bloqueos_cruzados = HorarioBloqueado.objects.filter(
                cancha=cancha,
                fecha=fecha,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            )

            if reservas_cruzadas.exists() or bloqueos_cruzados.exists():
                messages.error(request, 'Ese horario cruza con una reserva o bloqueo existente.')
            else:
                try:
                    with transaction.atomic():
                        bloqueo = form.save(commit=False)
                        bloqueo.cancha = cancha
                        bloqueo.save()
                    messages.success(request, 'Horario bloqueado correctamente.')
                    return redirect('canchas:horarios', cancha_id=cancha.id)
                except DatabaseError:
                    logger.exception('Error bloqueando horario para cancha %s', cancha_id)
                    messages.error(request, 'No se pudo bloquear el horario.')
    else:
        form = HorarioBloqueadoForm()

    try:
        horarios_bloqueados = (
            HorarioBloqueado.objects
            .filter(cancha=cancha)
            .order_by('fecha', 'hora_inicio')
        )
        reservas_ocupadas = (
            Reserva.objects
            .select_related('cliente', 'estado')
            .filter(cancha=cancha)
            .exclude(estado__nombre='Cancelada')
            .order_by('fecha', 'hora_inicio')[:20]
        )
    except DatabaseError:
        logger.exception('Error cargando horarios de cancha %s', cancha_id)
        messages.error(request, 'No se pudieron cargar los horarios.')
        horarios_bloqueados = reservas_ocupadas = []

    return render(
        request,
        'canchas/horarios.html',
        {
            'cancha': cancha,
            'form': form,
            'horarios_bloqueados': horarios_bloqueados,
            'reservas_ocupadas': reservas_ocupadas,
        },
    )


@operador_required
def eliminar_horario(request, horario_id):
    horario = get_object_or_404(HorarioBloqueado.objects.select_related('cancha'), pk=horario_id)
    cancha_id = horario.cancha_id

    if request.method == 'POST':
        try:
            horario.delete()
            messages.success(request, 'Horario liberado correctamente.')
            return redirect('canchas:horarios', cancha_id=cancha_id)
        except DatabaseError:
            logger.exception('Error eliminando horario bloqueado %s', horario_id)
            messages.error(request, 'No se pudo liberar el horario.')

    return render(request, 'canchas/confirm_delete_horario.html', {'horario': horario})


def detalle_cancha(request, cancha_id):
    cancha = get_object_or_404(
        Cancha.objects.select_related('estado').prefetch_related('reglas'),
        pk=cancha_id,
    )
    horarios_bloqueados = (
        HorarioBloqueado.objects
        .filter(cancha=cancha)
        .order_by('fecha', 'hora_inicio')[:10]
    )
    proximas_reservas = (
        Reserva.objects
        .select_related('estado')
        .filter(cancha=cancha)
        .exclude(estado__nombre='Cancelada')
        .order_by('fecha', 'hora_inicio')[:10]
    )

    context = {
        'cancha': cancha,
        'horarios_bloqueados': horarios_bloqueados,
        'proximas_reservas': proximas_reservas,
    }

    return render(request, 'canchas/detalle.html', context)


@admin_required
def reportes(request):
    try:
        total_reservas = Reserva.objects.count()
        ingresos = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0
        reservas_por_cancha = (
            Cancha.objects
            .annotate(total_reservas=Count('reserva'))
            .order_by('-total_reservas')[:5]
        )
        pagos_recientes = (
            Pago.objects
            .select_related('reserva', 'reserva__cancha', 'metodo_pago')
            .order_by('-fecha_pago')[:8]
        )
    except DatabaseError:
        logger.exception('Error cargando reportes')
        messages.error(request, 'No se pudieron cargar los reportes.')
        total_reservas = ingresos = 0
        reservas_por_cancha = pagos_recientes = []

    context = {
        'total_reservas': total_reservas,
        'ingresos': ingresos,
        'reservas_por_cancha': reservas_por_cancha,
        'pagos_recientes': pagos_recientes,
        'crecimiento': 15,
    }

    return render(request, 'canchas/reportes.html', context)
