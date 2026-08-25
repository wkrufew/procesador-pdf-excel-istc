import os
import re
from io import BytesIO

import pandas as pd
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from funciones.generador import limpiar_nombre

VARIABLE_PATTERN = re.compile(r"\{(\w+)\}")


def extraer_variables(plantilla_texto):
    """Devuelve la lista (sin duplicados, en orden) de variables {var} usadas en la plantilla."""
    vistos = []
    for var in VARIABLE_PATTERN.findall(plantilla_texto or ""):
        if var not in vistos:
            vistos.append(var)
    return vistos


def build_font_name(familia, negrita=False, cursiva=False):
    """Mapea familia + negrita/cursiva al nombre de fuente estándar de reportlab."""
    familia = familia or "Helvetica"
    if familia == "Times":
        base = "Times"
        if negrita and cursiva:
            return f"{base}-BoldItalic"
        if negrita:
            return f"{base}-Bold"
        if cursiva:
            return f"{base}-Italic"
        return f"{base}-Roman"

    # Helvetica y Courier comparten el mismo patrón de sufijos
    if negrita and cursiva:
        return f"{familia}-BoldOblique"
    if negrita:
        return f"{familia}-Bold"
    if cursiva:
        return f"{familia}-Oblique"
    return familia


def generar_qr_imagen(data, color="#000000"):
    """Genera un QR a partir de data (texto/URL) y devuelve un buffer PNG en memoria."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(data or "")
    qr.make(fit=True)
    img = qr.make_image(fill_color=color or "#000000", back_color="white").convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _valor_columna(row, columna):
    if not columna or columna not in row:
        return ""
    valor = row[columna]
    if pd.isna(valor):
        return ""
    return str(valor)


def _resolver_texto_parrafo(row, campo):
    texto = campo.get("plantilla_texto", "") or ""
    variables = campo.get("variables", {}) or {}
    for var, columna in variables.items():
        texto = texto.replace("{" + var + "}", _valor_columna(row, columna))
    # Acepta tanto Enter real como el texto literal "\n" escrito a mano
    texto = texto.replace("\\n", "\n")
    return texto


def create_overlay_pro(row, campos_pagina, page_width, page_height):
    """Genera un overlay de PDF dibujando todos los campos de una página."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for campo in campos_pagina:
        tipo = campo.get("tipo")

        if tipo in ("texto", "parrafo"):
            font_name = build_font_name(
                campo.get("font_familia", "Helvetica"),
                campo.get("negrita", False),
                campo.get("cursiva", False),
            )
            font_size = campo.get("font_size", 12)
            c.setFont(font_name, font_size)
            c.setFillColor(HexColor(campo.get("color") or "#000000"))
            centrado = campo.get("centrado", False)
            x = campo.get("x", 0)

            if tipo == "texto":
                valor = _valor_columna(row, campo.get("columna_excel"))
                if campo.get("formatear_nombre"):
                    valor = limpiar_nombre(valor)
                y = campo.get("y", 0)
                if centrado:
                    c.drawCentredString(page_width / 2, y, valor)
                else:
                    c.drawString(x, y, valor)
            else:  # parrafo
                texto = _resolver_texto_parrafo(row, campo)
                leading = campo.get("interlineado", font_size + 4)
                y = campo.get("y", 0)
                for linea in texto.split("\n"):
                    if centrado:
                        c.drawCentredString(page_width / 2, y, linea)
                    else:
                        c.drawString(x, y, linea)
                    y -= leading

        elif tipo == "qr":
            valor = _valor_columna(row, campo.get("columna_url"))
            if valor:
                qr_buffer = generar_qr_imagen(valor, campo.get("color") or "#000000")
                ancho = campo.get("ancho", 100)
                alto = campo.get("alto", 100)
                c.drawImage(
                    ImageReader(qr_buffer),
                    campo.get("x", 0),
                    campo.get("y", 0),
                    width=ancho,
                    height=alto,
                    mask="auto",
                )

    c.save()
    buffer.seek(0)
    return PdfReader(buffer)


def _nombre_archivo(row, idx, campos):
    for campo in campos:
        if campo.get("tipo") == "texto" and campo.get("usar_como_archivo"):
            valor = _valor_columna(row, campo.get("columna_excel"))
            if campo.get("formatear_nombre"):
                valor = limpiar_nombre(valor)
            valor = valor.strip()
            if valor:
                return valor
    return f"certificado_{idx + 1}"


def generar_certificados_pro(df, pdf_base_file, output_dir, campos):
    """Genera los PDFs aplicando una lista de campos genéricos (texto/parrafo/qr) por página."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    resultados = []

    if hasattr(pdf_base_file, "getvalue"):
        pdf_bytes = pdf_base_file.getvalue()
    else:
        pdf_bytes = pdf_base_file.read()

    for idx, row in df.iterrows():
        try:
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

            nombre = _nombre_archivo(row, idx, campos)
            file_path = os.path.join(output_dir, f"{nombre}.pdf")
            with open(file_path, "wb") as f:
                output.write(f)

            resultados.append({"Nombre": nombre, "Archivo": file_path})
            print(f"[{idx + 1}/{len(df)}] PDF generado: {file_path}")

        except Exception as e:
            print(f"Fila {idx + 1} error: {e}")
            continue

    print(f"✅ Generación finalizada. Total PDFs: {len(resultados)}")
    return pd.DataFrame(resultados)
