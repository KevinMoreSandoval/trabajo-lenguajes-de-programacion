from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, FloatField, Q, Sum, Value
from django.db.models.functions import Cast, Coalesce, TruncDate
from django.utils import timezone

from canchas.models import Cancha
from reservas.models import Reserva


ESTADOS_FINANCIEROS = ('Confirmada', 'Pagada', 'Finalizada')
ESTADOS_OPERATIVOS = ESTADOS_FINANCIEROS + ('Pendiente',)
MINUTOS_DISPONIBLES_DIA = 15 * 60


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _rango_fechas(filters):
    fecha = _parse_date(filters.get('fecha'))
    if fecha:
        return fecha, fecha

    desde = _parse_date(filters.get('fecha_desde'))
    hasta = _parse_date(filters.get('fecha_hasta'))
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde

    if not desde and not hasta:
        hasta = timezone.localdate()
        desde = hasta - timedelta(days=29)
    elif desde and not hasta:
        hasta = desde
    elif hasta and not desde:
        desde = hasta

    return desde, hasta


def _monto_expr():
    return Coalesce(
        'subtotal',
        'monto_total',
        Value(Decimal('0.00')),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _minutos_expr():
    return Coalesce(
        Cast('duracion_minutos', FloatField()),
        ExpressionWrapper(Cast(F('duracion_horas'), FloatField()) * Value(60.0), output_field=FloatField()),
        Value(0.0),
        output_field=FloatField(),
    )


def _base_queryset(filters=None, financiero=False):
    filters = filters or {}
    desde, hasta = _rango_fechas(filters)
    qs = Reserva.objects.select_related('cancha', 'cliente', 'estado')

    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)

    cancha_id = filters.get('cancha')
    usuario_id = filters.get('usuario')
    estado_id = filters.get('estado')

    if cancha_id:
        qs = qs.filter(cancha_id=cancha_id)
    if usuario_id:
        qs = qs.filter(cliente_id=usuario_id)
    if estado_id:
        qs = qs.filter(estado_id=estado_id)

    if financiero:
        qs = qs.filter(estado__nombre__in=ESTADOS_FINANCIEROS)

    return qs


def _as_float(value):
    if value is None:
        return 0.0
    return float(value)


def get_ingresos_por_dia(filters=None):
    qs = _base_queryset(filters, financiero=True)
    return [
        {'fecha': item['dia'].isoformat(), 'ingresos': _as_float(item['ingresos'])}
        for item in (
            qs.annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(ingresos=Sum(_monto_expr()))
            .order_by('dia')
        )
    ]


def get_ingresos_por_rango(filters=None):
    qs = _base_queryset(filters, financiero=True)
    data = qs.aggregate(ingresos=Coalesce(Sum(_monto_expr()), Value(Decimal('0.00'))))
    return _as_float(data['ingresos'])


def get_reservas_por_cancha(filters=None):
    qs = _base_queryset(filters, financiero=False)
    return [
        {
            'cancha': item['cancha__nombre'],
            'reservas': item['reservas'],
            'horas': round(_as_float(item['minutos']) / 60, 2),
        }
        for item in (
            qs.values('cancha__nombre')
            .annotate(reservas=Count('id'), minutos=Coalesce(Sum(_minutos_expr()), Value(0.0)))
            .order_by('-reservas', 'cancha__nombre')
        )
    ]


def get_ocupacion_por_cancha(filters=None):
    filters = filters or {}
    desde, hasta = _rango_fechas(filters)
    dias = max(((hasta - desde).days + 1), 1) if desde and hasta else 1
    minutos_periodo = dias * MINUTOS_DISPONIBLES_DIA

    qs = _base_queryset(filters, financiero=False).filter(estado__nombre__in=ESTADOS_OPERATIVOS)
    return [
        {
            'cancha': item['cancha__nombre'],
            'minutos_reservados': round(_as_float(item['minutos']), 2),
            'horas_reservadas': round(_as_float(item['minutos']) / 60, 2),
            'ocupacion': round(_as_float(item['ocupacion']), 2),
        }
        for item in (
            qs.values('cancha__nombre')
            .annotate(minutos=Coalesce(Sum(_minutos_expr()), Value(0.0)))
            .annotate(
                ocupacion=ExpressionWrapper(
                    F('minutos') * Value(100.0) / Value(float(minutos_periodo)),
                    output_field=FloatField(),
                )
            )
            .order_by('-ocupacion', 'cancha__nombre')
        )
    ]


def get_top_canchas(filters=None, limit=5):
    qs = _base_queryset(filters, financiero=True)
    return [
        {
            'cancha': item['cancha__nombre'],
            'ingresos': _as_float(item['ingresos']),
            'reservas': item['reservas'],
        }
        for item in (
            qs.values('cancha__nombre')
            .annotate(ingresos=Coalesce(Sum(_monto_expr()), Value(Decimal('0.00'))), reservas=Count('id'))
            .order_by('-ingresos', 'cancha__nombre')[:limit]
        )
    ]


def get_horas_vendidas_por_dia(filters=None):
    qs = _base_queryset(filters, financiero=True)
    return [
        {'fecha': item['dia'].isoformat(), 'horas': round(_as_float(item['minutos']) / 60, 2)}
        for item in (
            qs.annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(minutos=Coalesce(Sum(_minutos_expr()), Value(0.0)))
            .order_by('dia')
        )
    ]


def get_kpis(filters=None):
    filters = filters or {}
    desde, hasta = _rango_fechas(filters)
    dias = max(((hasta - desde).days + 1), 1) if desde and hasta else 1
    cancha_id = filters.get('cancha')
    canchas_count = Cancha.objects.filter(id=cancha_id).count() if cancha_id else Cancha.objects.count()
    capacidad_total = max(canchas_count * dias * MINUTOS_DISPONIBLES_DIA, 1)

    qs_financiero = _base_queryset(filters, financiero=True)
    fin = qs_financiero.aggregate(
        ingresos=Coalesce(Sum(_monto_expr()), Value(Decimal('0.00'))),
        reservas=Count('id'),
        minutos=Coalesce(Sum(_minutos_expr()), Value(0.0)),
    )

    qs_ocupacion = _base_queryset(filters, financiero=False).filter(estado__nombre__in=ESTADOS_OPERATIVOS)
    ocup = qs_ocupacion.aggregate(minutos=Coalesce(Sum(_minutos_expr()), Value(0.0)))

    horas_vendidas = _as_float(fin['minutos']) / 60
    ocupacion = (_as_float(ocup['minutos']) / capacidad_total) * 100

    return {
        'ingresos_totales': _as_float(fin['ingresos']),
        'ingresos_rango': get_ingresos_por_rango(filters),
        'total_reservas': fin['reservas'],
        'horas_vendidas': round(horas_vendidas, 2),
        'tasa_ocupacion': round(ocupacion, 2),
        'canchas_rentables': get_top_canchas(filters, limit=5),
        'rango': {'desde': desde.isoformat() if desde else '', 'hasta': hasta.isoformat() if hasta else ''},
    }
