import io
from typing import Callable, Iterable

from openpyxl import Workbook

HEADERS = ["Data/Hora", "Equipamento", "Canal", "Nome do canal", "Temperatura (C)", "Umidade (%)"]
WIDTHS = (20, 18, 8, 22, 16, 12)


def build_xlsx(rows: Iterable, channel_label: Callable[[int], str]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Leituras"
    ws.append(HEADERS)
    for r in rows:
        ws.append([r.recorded_at, r.device_name, r.channel, channel_label(r.channel),
                   r.temperature_c, r.humidity])
    for letter, width in zip("ABCDEF", WIDTHS):
        ws.column_dimensions[letter].width = width
    for cell in ws["A"][1:]:
        cell.number_format = "dd/mm/yyyy hh:mm:ss"
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
