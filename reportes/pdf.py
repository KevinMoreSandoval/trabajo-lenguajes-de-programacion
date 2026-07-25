import unicodedata
from django.utils import timezone


def _simple_pdf(lines):
    """Genera un PDF de texto paginado sin dependencias externas."""

    def clean(value):
        text = (
            unicodedata.normalize("NFKD", str(value))
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    chunks = [lines[index : index + 46] for index in range(0, len(lines), 46)] or [[]]
    objects = [None, None]
    page_ids = []
    content_ids = []
    font_id = 3 + len(chunks) * 2
    for index, chunk in enumerate(chunks):
        page_id = 3 + index * 2
        content_id = page_id + 1
        page_ids.append(page_id)
        content_ids.append(content_id)
        commands = ["BT", "/F1 10 Tf", "45 800 Td", "13 TL"]
        for line in chunk:
            commands.append(f"({clean(line)}) Tj T*")
        commands.append("ET")
        stream = "\n".join(commands).encode()
        objects.extend(
            [
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode(),
                b"<< /Length "
                + str(len(stream)).encode()
                + b" >>\nstream\n"
                + stream
                + b"\nendstream",
            ]
        )
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        f'<< /Type /Pages /Kids [{" ".join(f"{item} 0 R" for item in page_ids)}] /Count {len(page_ids)} >>'.encode()
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return bytes(output)


def _reservations_report_pdf(reservations, start, end, total):
    """PDF visual con resumen, tabla paginada y pie de página."""

    def clean(value):
        return (
            unicodedata.normalize("NFKD", str(value))
            .encode("ascii", "ignore")
            .decode("ascii")
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

    def text(x, y, value, size=9, bold=False, color="0.15 0.2 0.28"):
        font = "F2" if bold else "F1"
        return f"BT {color} rg /{font} {size} Tf {x} {y} Td ({clean(value)}) Tj ET"

    rows = list(reservations)
    paid_count = sum(1 for item in rows if item.monto_pagado > 0)
    page_rows = [rows[index : index + 24] for index in range(0, len(rows), 24)] or [[]]
    streams = []
    for page_number, chunk in enumerate(page_rows, 1):
        commands = [
            "0.02 0.64 0.40 rg 0 758 595 84 re f",
            text(38, 810, "KANCHA SPORTS", 18, True, "1 1 1"),
            text(38, 789, "REPORTE DE RESERVAS Y PAGOS", 9, True, "0.82 1 0.91"),
            text(390, 807, f"{start:%d/%m/%Y} - {end:%d/%m/%Y}", 10, True, "1 1 1"),
            text(
                390,
                789,
                f"Generado: {timezone.localtime():%d/%m/%Y %H:%M}",
                7,
                False,
                "0.82 1 0.91",
            ),
            "0.95 0.98 0.96 rg 32 682 164 58 re f",
            "0.95 0.98 0.96 rg 215 682 164 58 re f",
            "0.95 0.98 0.96 rg 398 682 164 58 re f",
            text(46, 718, "RESERVAS", 7, True, "0.36 0.44 0.52"),
            text(46, 694, len(rows), 20, True, "0.02 0.55 0.34"),
            text(229, 718, "CON PAGOS", 7, True, "0.36 0.44 0.52"),
            text(229, 694, paid_count, 20, True, "0.02 0.55 0.34"),
            text(412, 718, "TOTAL COBRADO", 7, True, "0.36 0.44 0.52"),
            text(412, 694, f"S/ {total}", 18, True, "0.02 0.55 0.34"),
            text(34, 654, "DETALLE DE OPERACIONES", 10, True),
            "0.91 0.94 0.97 rg 32 619 531 25 re f",
            text(40, 628, "RESERVA", 7, True, "0.3 0.4 0.52"),
            text(90, 628, "FECHA / HORA", 7, True, "0.3 0.4 0.52"),
            text(170, 628, "CLIENTE", 7, True, "0.3 0.4 0.52"),
            text(315, 628, "CANCHA", 7, True, "0.3 0.4 0.52"),
            text(420, 628, "ESTADO", 7, True, "0.3 0.4 0.52"),
            text(505, 628, "PAGADO", 7, True, "0.3 0.4 0.52"),
        ]
        y = 596
        for index, item in enumerate(chunk):
            if index % 2:
                commands.append(f"0.975 0.985 0.98 rg 32 {y-7} 531 22 re f")
            client = (item.cliente.get_full_name() or item.cliente.email)[:25]
            commands.extend(
                [
                    text(40, y, f"#{item.pk:05d}", 7, True),
                    text(90, y, f"{item.fecha:%d/%m/%Y} {item.hora_inicio:%H:%M}", 7),
                    text(170, y, client, 7),
                    text(315, y, item.cancha.nombre[:18], 7),
                    text(420, y, item.estado.nombre[:12], 7),
                    text(505, y, f"S/ {item.monto_pagado}", 7, True),
                    f"0.88 0.91 0.94 RG 32 {y-9} m 563 {y-9} l S",
                ]
            )
            y -= 23
        if not chunk:
            commands.append(
                text(
                    210,
                    575,
                    "No hay reservas en el periodo seleccionado.",
                    9,
                    False,
                    "0.4 0.46 0.55",
                )
            )
        commands.extend(
            [
                "0.02 0.64 0.40 rg 0 0 595 30 re f",
                text(
                    32,
                    11,
                    "Kancha Sports - Documento administrativo",
                    7,
                    False,
                    "1 1 1",
                ),
                text(520, 11, f"{page_number}/{len(page_rows)}", 7, True, "1 1 1"),
            ]
        )
        streams.append("\n".join(commands).encode())

    objects = [None, None]
    page_ids = []
    font_regular_id = 3 + len(streams) * 2
    font_bold_id = font_regular_id + 1
    for index, stream in enumerate(streams):
        page_id = 3 + index * 2
        content_id = page_id + 1
        page_ids.append(page_id)
        objects.extend(
            [
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> /Contents {content_id} 0 R >>".encode(),
                b"<< /Length "
                + str(len(stream)).encode()
                + b" >>\nstream\n"
                + stream
                + b"\nendstream",
            ]
        )
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        f'<< /Type /Pages /Kids [{" ".join(f"{item} 0 R" for item in page_ids)}] /Count {len(page_ids)} >>'.encode()
    )
    objects.extend(
        [
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ]
    )
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return bytes(output)
