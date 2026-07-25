import unicodedata

from django.utils import timezone


def _clean(value):
    return (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def build_payment_receipt(pago):
    reserva = pago.reserva
    cliente = reserva.cliente.get_full_name() or reserva.cliente.email
    saldo = reserva.monto_total - reserva.monto_pagado

    def text(x, y, value, size=10, bold=False, color="0.12 0.18 0.25"):
        font = "F2" if bold else "F1"
        return f"BT {color} rg /{font} {size} Tf {x} {y} Td ({_clean(value)}) Tj ET"

    commands = [
        "0.02 0.64 0.40 rg 0 720 595 122 re f",
        text(42, 790, "KANCHA SPORTS", 22, True, "1 1 1"),
        text(42, 765, "BOLETA DE PAGO", 11, True, "0.82 1 0.91"),
        text(430, 790, f"N. B-{pago.pk:06d}", 11, True, "1 1 1"),
        text(
            430,
            770,
            f"{timezone.localtime(pago.fecha_pago):%d/%m/%Y %H:%M}",
            8,
            False,
            "0.82 1 0.91",
        ),
        "0.94 0.98 0.96 rg 36 625 523 70 re f",
        text(52, 670, "MONTO PAGADO", 8, True, "0.35 0.43 0.5"),
        text(52, 642, f"S/ {pago.monto}", 25, True, "0.02 0.55 0.34"),
        text(350, 670, "METODO", 8, True, "0.35 0.43 0.5"),
        text(350, 645, pago.metodo_pago.nombre, 15, True),
        text(42, 590, "DATOS DEL CLIENTE", 10, True, "0.02 0.55 0.34"),
        text(42, 565, "Cliente", 8, True, "0.4 0.46 0.54"),
        text(170, 565, cliente, 10),
        text(42, 540, "DNI", 8, True, "0.4 0.46 0.54"),
        text(170, 540, reserva.cliente.dni or "-", 10),
        text(42, 500, "DETALLE DE LA RESERVA", 10, True, "0.02 0.55 0.34"),
        text(42, 475, "Reserva", 8, True, "0.4 0.46 0.54"),
        text(170, 475, f"#{reserva.pk:05d}", 10),
        text(42, 450, "Cancha", 8, True, "0.4 0.46 0.54"),
        text(170, 450, reserva.cancha.nombre, 10),
        text(42, 425, "Fecha y horario", 8, True, "0.4 0.46 0.54"),
        text(
            170,
            425,
            f"{reserva.fecha:%d/%m/%Y}  {reserva.hora_inicio:%H:%M}-{reserva.hora_fin:%H:%M}",
            10,
        ),
        text(42, 400, "Total reserva", 8, True, "0.4 0.46 0.54"),
        text(170, 400, f"S/ {reserva.monto_total}", 10),
        text(42, 375, "Saldo pendiente", 8, True, "0.4 0.46 0.54"),
        text(170, 375, f"S/ {saldo}", 10, True),
        text(42, 335, "DATOS DE LA OPERACION", 10, True, "0.02 0.55 0.34"),
        text(42, 310, "Codigo", 8, True, "0.4 0.46 0.54"),
        text(170, 310, pago.codigo_operacion or "Pago en efectivo", 10),
        "0.02 0.64 0.40 rg 0 0 595 44 re f",
        text(42, 18, "Gracias por confiar en Kancha Sports.", 9, True, "1 1 1"),
    ]
    stream = "\n".join(commands).encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(b"xref\n0 7\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return bytes(output)
