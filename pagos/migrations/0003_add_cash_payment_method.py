from django.db import migrations


def add_cash_method(apps, schema_editor):
    TipoMetodoPago = apps.get_model('pagos', 'TipoMetodoPago')
    MetodoPago = apps.get_model('pagos', 'MetodoPago')
    cash_type, _ = TipoMetodoPago.objects.get_or_create(nombre='Efectivo')
    MetodoPago.objects.update_or_create(
        nombre='Efectivo',
        defaults={'tipo': cash_type, 'activo': True},
    )


def remove_cash_method(apps, schema_editor):
    MetodoPago = apps.get_model('pagos', 'MetodoPago')
    MetodoPago.objects.filter(nombre='Efectivo').delete()


class Migration(migrations.Migration):
    dependencies = [('pagos', '0002_pagobilletera_pagotarjeta_alter_estadopago_options_and_more')]
    operations = [migrations.RunPython(add_cash_method, remove_cash_method)]
