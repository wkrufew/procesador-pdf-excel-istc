from io import BytesIO

from PyPDF2 import PdfReader, PdfWriter

from funciones.generador_pro import create_overlay_pro


def generar_pdf_preview_bytes(row, pdf_base_file, campos):
    """Genera el PDF fusionado de una sola fila (ej. la primera del Excel) en memoria,
    sin escribir a disco. Se usa para la vista previa de impresión."""
    if hasattr(pdf_base_file, "getvalue"):
        pdf_bytes = pdf_base_file.getvalue()
    else:
        pdf_bytes = pdf_base_file.read()

    base_pdf = PdfReader(BytesIO(pdf_bytes))
    output = PdfWriter()

    for page_idx in range(len(base_pdf.pages)):
        pagina_num = page_idx + 1
        page = base_pdf.pages[page_idx]
        campos_pagina = [c for c in campos if c.get("pagina") == pagina_num]

        if campos_pagina:
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            overlay = create_overlay_pro(row, campos_pagina, page_width, page_height)
            page.merge_page(overlay.pages[0])

        output.add_page(page)

    buffer = BytesIO()
    output.write(buffer)
    buffer.seek(0)
    return buffer.getvalue()
