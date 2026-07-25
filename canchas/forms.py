from datetime import datetime

from django import forms
from django.utils import timezone

from reservas.forms import HORA_APERTURA, HORA_CIERRE, INTERVALO_MINUTOS

from .models import Cancha, HorarioBloqueado


class CanchaForm(forms.ModelForm):
    techada = forms.TypedChoiceField(
        choices=((True, 'Techada'), (False, 'No techada')),
        coerce=lambda value: value == 'True',
        label='Techada',
    )
    iluminacion = forms.TypedChoiceField(
        choices=((True, 'Iluminacion LED'), (False, 'Sin iluminacion')),
        coerce=lambda value: value == 'True',
        label='Iluminacion',
    )
    banos = forms.TypedChoiceField(
        choices=((True, 'Vestuarios incluidos'), (False, 'Sin vestuarios')),
        coerce=lambda value: value == 'True',
        label='Vestuarios',
    )

    class Meta:
        model = Cancha
        fields = (
            'estado',
            'nombre',
            'tipo',
            'capacidad',
            'precio_por_hora',
            'ubicacion',
            'imagen_url',
            'descripcion',
            'techada',
            'iluminacion',
            'banos',
            'ancho',
            'largo',
            'reglas',
        )
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'reglas': forms.CheckboxSelectMultiple,
        }
        labels = {
            'nombre': 'Nombre',
            'tipo': 'Tipo',
            'precio_por_hora': 'Precio por hora',
            'estado': 'Estado',
            'ubicacion': 'Ubicacion',
            'capacidad': 'Capacidad jugadores',
            'ancho': 'Ancho',
            'largo': 'Largo',
            'imagen_url': 'URL de imagen',
        }


class HorarioBloqueadoForm(forms.ModelForm):
    class Meta:
        model = HorarioBloqueado
        fields = ('fecha', 'hora_inicio', 'hora_fin', 'motivo')
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
            'motivo': forms.TextInput(attrs={'placeholder': 'Mantenimiento, evento privado, limpieza...'}),
        }

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < timezone.localdate():
            raise forms.ValidationError('No puedes bloquear fechas pasadas.')
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
            raise forms.ValidationError('Los bloqueos deben estar entre 08:00 y 23:00.')

        if hora_inicio.minute not in (0, 30) or hora_fin.minute not in (0, 30):
            raise forms.ValidationError('Los bloqueos deben estar en rangos de 30 minutos.')

        if datetime.combine(fecha, hora_fin).date() != fecha:
            raise forms.ValidationError('El bloqueo debe terminar el mismo dia.')

        duracion_minutos = int((datetime.combine(fecha, hora_fin) - datetime.combine(fecha, hora_inicio)).total_seconds() // 60)
        if duracion_minutos < INTERVALO_MINUTOS or duracion_minutos % INTERVALO_MINUTOS:
            raise forms.ValidationError('El bloqueo minimo es de 30 minutos y debe avanzar de 30 en 30.')

        return cleaned_data
