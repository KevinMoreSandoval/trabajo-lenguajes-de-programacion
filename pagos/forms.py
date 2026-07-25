from django import forms

from .models import MetodoPago


class PagoForm(forms.Form):
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodoPago.objects.none(),
        label='Metodo de pago',
        empty_label='Selecciona un metodo',
        widget=forms.RadioSelect,
    )
    monto = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label='Monto a pagar',
    )
    referencia = forms.CharField(required=False, max_length=100, label='Referencia')
    codigo_operacion = forms.CharField(required=False, max_length=100, label='Codigo de operacion')
    observacion = forms.CharField(required=False, max_length=255, label='Observacion')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metodo_pago'].queryset = MetodoPago.objects.filter(activo=True).order_by('nombre')
