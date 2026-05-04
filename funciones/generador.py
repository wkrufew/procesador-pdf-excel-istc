import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
import unicodedata

def limpiar_nombre(nombre):
    if not nombre:
        return ''
    nombre = str(nombre).strip()
    nombre = " ".join(nombre.split())
    nombre = nombre.upper()
    return nombre

def create_overlay(name, final_grade=None, page=1, config=None):
    """
    Genera un overlay de PDF con nombre y nota según la página y configuración.
    """
    try:
        buffer = BytesIO()
        orientation = config.get('orientation', 'HORIZONTAL')
        page_width, page_height = (842, 595) if orientation == "HORIZONTAL" else (595, 842)
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Nombre (página 1)
        if page == 1 and 'nombre' in config:
            conf = config['nombre']
            c.setFont(conf.get('font', 'Helvetica-Bold'), conf.get('font_size', 18))
            y_pos = conf.get('y', int(page_height/2))

            if conf.get('centrado', True):
                c.drawCentredString(page_width/2, y_pos, name)
            else:
                x_pos = conf.get('x', 50)
                c.drawString(x_pos, y_pos, name)

        # Nota (página 2)
        if page == 2 and final_grade is not None and 'nota' in config:
            conf = config['nota']
            c.setFont(conf.get('font', 'Helvetica'), conf.get('font_size', 12))
            y_pos = conf.get('y', int(page_height/10))

            if conf.get('centrado', True):
                c.drawCentredString(page_width/2, y_pos, str(final_grade))
            else:
                x_pos = conf.get('x', 50)
                c.drawString(x_pos, y_pos, str(final_grade))

        c.save()
        buffer.seek(0)
        return PdfReader(buffer)   # Ahora sí contiene el texto
    except Exception as e:
        raise RuntimeError(f"Error creando overlay: {e}")

def generar_certificados(df, pdf_base_file, output_dir, col_nombre, col_nota,
                         config_nombre, config_nota, orientation):
    """
    Genera los PDFs usando las configuraciones ingresadas.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    resultados = []

    # ✅ Leer PDF base una sola vez en memoria (con getvalue)
    if hasattr(pdf_base_file, "getvalue"):
        pdf_bytes = pdf_base_file.getvalue()
    else:
        pdf_bytes = pdf_base_file.read()

    for idx, row in df.iterrows():
        try:
            name = limpiar_nombre(str(row[col_nombre]))
            final_grade = row[col_nota] if col_nota else None
            if not name:
                continue

            # Crear lector nuevo desde los mismos bytes en cada iteración
            base_pdf = PdfReader(BytesIO(pdf_bytes))
            output = PdfWriter()
            full_config = {
                'nombre': config_nombre,
                'nota': config_nota,
                'orientation': orientation
            }

            # Página 1 → Nombre
            overlay1 = create_overlay(name, final_grade, 1, full_config)
            page1 = base_pdf.pages[0]
            page1.merge_page(overlay1.pages[0])
            output.add_page(page1)

            # Página 2 → Nota
            if len(base_pdf.pages) > 1:
                overlay2 = create_overlay(name, final_grade, 2, full_config)
                page2 = base_pdf.pages[1]
                page2.merge_page(overlay2.pages[0])
                output.add_page(page2)

            # Guardar con nombre en mayúsculas
            safe_name = f"{name}.pdf"
            file_path = os.path.join(output_dir, safe_name)
            with open(file_path, "wb") as f:
                output.write(f)

            resultados.append({'Nombre': name, 'Archivo': file_path})
            print(f"[{idx+1}/{len(df)}] PDF generado: {file_path}")

        except Exception as e:
            print(f"Fila {idx+1} error: {e}")
            continue

    print(f"✅ Generación finalizada. Total PDFs: {len(resultados)}")
    return pd.DataFrame(resultados)
