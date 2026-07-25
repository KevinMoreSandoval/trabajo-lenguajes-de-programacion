from django.http import HttpResponse

from .pdf import build_payment_receipt


def payment_receipt_response(pago):
    response = HttpResponse(build_payment_receipt(pago), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="boleta_B-{pago.pk:06d}.pdf"'
    )
    return response
