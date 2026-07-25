from datetime import datetime, time, timedelta
from decimal import Decimal

from django import forms
from django.utils import timezone

from authentication.models import Usuario
from canchas.models import Cancha
from pagos.models import MetodoPago


HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(23, 0)
INTERVALO_MINUTOS = 30
MIN_DURACION_MINUTOS = 60
MAX_DURACION_HORAS = Decimal('5.00')


def generar_horas_predeterminadas():
    horas = []
    inicio = datetime.combine(timezone.localdate(), HORA_APERTURA)
    cierre = datetime.combine(timezone.localdate(), HORA_CIERRE)
    while inicio < cierre:
        horas.append(inicio.time())
        inicio += timedelta(minutes=INTERVALO_MINUTOS)
    return horas


def etiqueta_duracion(valor):
    horas = int(valor)
    minutos = int((valor - Decimal(horas)) * Decimal('60'))
    partes = []
    if horas:
        partes.append(f'{horas} hora' if horas == 1 else f'{horas} horas')
    if minutos:
        partes.append(f'{minutos} min')
    return ' '.join(partes)


DURACIONES = tuple(
    (Decimal(minutos) / Decimal('60'), etiqueta_duracion(Decimal(minutos) / Decimal('60')))
    for minutos in range(MIN_DURACION_MINUTOS, int(MAX_DURACION_HORAS * Decimal('60')) + INTERVALO_MINUTOS, INTERVALO_MINUTOS)
)


class ReservaForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        required=False,
        label='Cliente',
        empty_label='Selecciona un cliente',
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha',
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label='Hora inicio',
    )
    duracion_horas = forms.ChoiceField(
        choices=DURACIONES,
        label='Duracion en horas',
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Observaciones',
    )

    def __init__(self, *args, **kwargs):
        self.es_operador = kwargs.pop('es_operador', False)
        super().__init__(*args, **kwargs)
        if self.es_operador:
            self.fields['cliente'].queryset = (
                Usuario.objects
                .select_related('rol')
                .filter(rol__nombre='Cliente', activo=True)
                .order_by('first_name', 'last_name', 'email')
            )
            self.fields['cliente'].required = True
        else:
            self.fields.pop('cliente')

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < timezone.localdate():
            raise forms.ValidationError('No puedes reservar fechas pasadas.')
        return fecha

    def clean_duracion_horas(self):
        return Decimal(self.cleaned_data['duracion_horas'])

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        duracion_horas = cleaned_data.get('duracion_horas')
        if not fecha or not hora_inicio or not duracion_horas:
            return cleaned_data

        inicio_dt = datetime.combine(fecha, hora_inicio)
        fin_dt = inicio_dt + timedelta(minutes=int(duracion_horas * Decimal('60')))
        hora_fin = fin_dt.time()

        if hora_inicio.minute not in (0, 30):
            raise forms.ValidationError('La hora de inicio debe estar en rangos de 30 minutos.')

        if hora_inicio < HORA_APERTURA or hora_fin > HORA_CIERRE or fin_dt.date() != fecha:
            raise forms.ValidationError('El horario debe estar entre 08:00 y 23:00 del mismo dia.')

        cleaned_data['hora_fin'] = hora_fin
        return cleaned_data


class BuscarClienteForm(forms.Form):
    dni = forms.CharField(
        label='DNI del cliente',
        min_length=8,
        max_length=8,
        widget=forms.TextInput(attrs={'placeholder': 'Ingresa el DNI de 8 digitos'}),
    )

    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if not dni.isdigit():
            raise forms.ValidationError('El DNI debe contener solo numeros.')
        return dni


class ReservaRecepcionForm(forms.Form):
    cancha = forms.ModelChoiceField(
        queryset=Cancha.objects.none(),
        label='Cancha',
        empty_label='Selecciona una cancha',
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha',
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label='Hora inicio',
    )
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label='Hora fin',
    )
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodoPago.objects.none(),
        label='Metodo de pago',
        empty_label=None,
    )
    observaciones = forms.CharField(
        required=False,
        max_length=255,
        label='Observaciones',
        widget=forms.TextInput(attrs={'placeholder': 'Notas adicionales opcional'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cancha'].queryset = Cancha.objects.select_related('estado').order_by('nombre')
        self.fields['metodo_pago'].queryset = MetodoPago.objects.filter(activo=True).order_by('nombre')

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < timezone.localdate():
            raise forms.ValidationError('No puedes reservar fechas pasadas.')
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        if not fecha or not hora_inicio or not hora_fin:
            return cleaned_data

        if hora_inicio >= hora_fin:
            raise forms.ValidationError('La hora de fin debe ser mayor que la hora de inicio.')
        if hora_inicio < HORA_APERTURA or hora_fin > HORA_CIERRE:
            raise forms.ValidationError('El horario debe estar entre 08:00 y 23:00.')
        if hora_inicio.minute not in (0, 30) or hora_fin.minute not in (0, 30):
            raise forms.ValidationError('Los horarios deben estar en rangos de 30 minutos.')

        inicio_dt = datetime.combine(fecha, hora_inicio)
        fin_dt = datetime.combine(fecha, hora_fin)
        duracion_minutos = int((fin_dt - inicio_dt).total_seconds() // 60)
        if duracion_minutos < MIN_DURACION_MINUTOS:
            raise forms.ValidationError('La reserva minima es de 1 hora.')
        if duracion_minutos % INTERVALO_MINUTOS:
            raise forms.ValidationError('La duracion debe avanzar en rangos de 30 minutos.')
        cleaned_data['duracion_horas'] = Decimal(duracion_minutos) / Decimal('60')
        return cleaned_data


class ReservaMultipleForm(forms.Form):
    items_json = forms.CharField(widget=forms.HiddenInput)
