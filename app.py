import json
import re
from io import BytesIO
import streamlit as st
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader
from funciones.generador import generar_certificados
from funciones import generador_pro, generador_avanzado, renombrador, correos
from utils.coordinates import mostrar_captura_coordenadas, create_hover_image
from streamlit_image_coordinates import streamlit_image_coordinates
from pdf2image import convert_from_bytes
import os

# Configurar la ruta de Poppler: en Windows hace falta la ruta explícita del binario
# descargado aparte; en Linux (VPS) ya queda en el PATH del sistema vía apt install
# poppler-utils, así que None deja que pdf2image lo encuentre solo.
POPPLER_PATH = r'C:\poppler\Library\bin' if os.name == 'nt' else None

# Configuración inicial
st.set_page_config(page_title="ISTCUMANDA", page_icon="📘", layout="centered")
st.title("📘 Herramientas ISTCUMANDA")

# --- Menú lateral ---
opcion = st.sidebar.radio("Selecciona opción", [
    "Inicio",
    "Generador de Certificados",
    "Generador de Certificados (Pro)",
    "Generador de PDF Avanzado",
    "Renombrador de PDFs",
    "Envio Masivo de Correos",
    "Envio Masivo de WhatsApp",  # 🔹 NUEVA OPCIÓN
    "Generador CSV Moodle"
])

# --- Página de inicio ---
if opcion == "Inicio":
    st.image("assets/logo.png", width=180)
    st.markdown(
        "<h1 style='text-align: center;'>📘 Herramientas ISTCUMANDA</h1>"
        "<p style='text-align: center;'>Bienvenido a la aplicación de certificados personalizados.</p>",
        unsafe_allow_html=True
    )

# --- Generador de certificados ---
elif opcion == "Generador de Certificados":
    st.header("🔹 Generador de Certificados")
    
    uploaded_file = st.file_uploader("Sube Excel con Nombres y Nota", type=["xlsx","xlsm","csv"])
    pdf_base_file = st.file_uploader("Sube PDF base", type=["pdf"])
    output_dir = st.text_input("Carpeta de salida")

    if uploaded_file and pdf_base_file and output_dir:
        # Leer Excel
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=";", dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str, engine="openpyxl")

        # Columnas
        col_nombre = st.selectbox("Columna con Nombres", df.columns)
        col_nota = st.selectbox("Columna con Nota (opcional)", [None] + list(df.columns))

        # Orientación PDF
        orientation = st.selectbox("Orientación PDF", ["HORIZONTAL","VERTICAL"])

        # --- Previsualización PDF ---
        st.subheader("📄 Previsualización PDF con coordenadas")
        try:
            pdf_bytes = pdf_base_file.read()
            pages = convert_from_bytes(pdf_bytes, dpi=150, poppler_path=POPPLER_PATH)
            page1_img = pages[0]
            page2_img = pages[1] if len(pages) > 1 else None
            coords_nombre, coords_nota = mostrar_captura_coordenadas(page1_img, page2_img, col_nota, orientation)
        except Exception as e:
            st.error(f"No se pudo previsualizar PDF: {e}")
            st.info(f"Verifica Poppler en: {POPPLER_PATH or 'PATH del sistema'} -> {os.path.exists(POPPLER_PATH) if POPPLER_PATH else 'revisar instalacion de poppler-utils'}")
            coords_nombre, coords_nota = (None, None), (None, None)

        # --- Configuración de fuentes ---
        st.subheader("🎨 Configuración de fuentes")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Nombre (Página 1)**")
            font_name = st.selectbox("Fuente Nombre", ["Helvetica-Bold","Times-Bold","Courier-Bold"])
            font_size = st.number_input("Tamaño Fuente", min_value=6, max_value=72, value=18)
            nombre_centrado = st.checkbox("Centrar Nombre", value=True, key="centrar_nombre")
        with col2:
            if col_nota:
                st.write("**Nota (Página 2)**")
                font_nota = st.selectbox("Fuente Nota", ["Helvetica","Times-Roman","Courier"])
                font_size_nota = st.number_input("Tamaño Fuente Nota", min_value=6, max_value=72, value=12)
                nota_centrado = st.checkbox("Centrar Nota", value=False, key="centrar_nota")
            else:
                font_nota = font_size_nota = None
                nota_centrado = None

        # --- Construir configuraciones ---
        config_nombre = {
            'x': coords_nombre[0],
            'y': coords_nombre[1],
            'centrado': nombre_centrado,
            'font': font_name,
            'font_size': font_size
        }
        config_nota = {}
        if col_nota:
            config_nota = {
                'x': coords_nota[0],
                'y': coords_nota[1],
                'centrado': nota_centrado,
                'font': font_nota,
                'font_size': font_size_nota
            }

        # --- Botón generar ---
        if st.button("🚀 Generar Certificados"):
            resultados = generar_certificados(
                df, pdf_base_file, output_dir,
                col_nombre, col_nota,
                config_nombre, config_nota,
                orientation
            )
            st.success(f"✅ Generados {len(resultados)} PDFs en: {output_dir}")
            st.dataframe(resultados)

# --- Generador de certificados (Pro) ---
elif opcion == "Generador de Certificados (Pro)":
    st.header("🔹 Generador de Certificados (Pro)")
    st.caption(
        "Campos dinámicos ilimitados: texto, párrafo con variables ({variable}) y código QR. "
        "No afecta al Generador de Certificados clásico."
    )

    uploaded_file_pro = st.file_uploader("Sube Excel con los datos", type=["xlsx", "xlsm", "csv"], key="pro_excel")
    pdf_base_file_pro = st.file_uploader("Sube PDF base", type=["pdf"], key="pro_pdf")
    output_dir_pro = st.text_input("Carpeta de salida", key="pro_output_dir")

    st.session_state.setdefault("campos_pro", [])

    with st.expander("📂 Cargar plantilla guardada"):
        plantilla_file = st.file_uploader("Archivo de plantilla (.json)", type=["json"], key="pro_plantilla_upload")
        if plantilla_file and st.button("Aplicar plantilla cargada"):
            try:
                st.session_state["campos_pro"] = json.load(plantilla_file)
                st.success("Plantilla cargada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo leer la plantilla: {e}")

    if uploaded_file_pro and pdf_base_file_pro and output_dir_pro:
        if uploaded_file_pro.name.endswith(".csv"):
            df_pro = pd.read_csv(uploaded_file_pro, sep=";", dtype=str)
        else:
            df_pro = pd.read_excel(uploaded_file_pro, dtype=str, engine="openpyxl")

        pdf_bytes_pro = pdf_base_file_pro.getvalue()

        # --- Previsualización + dimensiones reales de cada página ---
        paginas_img = []
        paginas_dims = []
        try:
            paginas_img = convert_from_bytes(pdf_bytes_pro, dpi=150, poppler_path=POPPLER_PATH)
            base_pdf_reader = PdfReader(BytesIO(pdf_bytes_pro))
            paginas_dims = [(float(p.mediabox.width), float(p.mediabox.height)) for p in base_pdf_reader.pages]
        except Exception as e:
            st.error(f"No se pudo previsualizar el PDF: {e}")
            st.info(f"Verifica Poppler en: {POPPLER_PATH or 'PATH del sistema'} -> {os.path.exists(POPPLER_PATH) if POPPLER_PATH else 'revisar instalacion de poppler-utils'}")

        num_paginas = max(len(paginas_img), 1)

        st.subheader("🧩 Campos del certificado")
        if st.button("➕ Agregar campo"):
            primera_col = df_pro.columns[0] if len(df_pro.columns) else ""
            st.session_state["campos_pro"].append({
                "nombre_campo": f"Campo {len(st.session_state['campos_pro']) + 1}",
                "tipo": "texto",
                "pagina": 1,
                "x": 50, "y": 50,
                "centrado": False,
                "font_familia": "Helvetica",
                "font_size": 14,
                "negrita": False,
                "cursiva": False,
                "columna_excel": primera_col,
                "usar_como_archivo": False,
                "formatear_nombre": False,
                "plantilla_texto": "",
                "variables": {},
                "interlineado": 18,
                "columna_url": primera_col,
                "ancho": 100,
                "alto": 100,
            })
            st.rerun()

        campos = st.session_state["campos_pro"]
        eliminar_idx = None

        for i, campo in enumerate(campos):
            with st.expander(f"🔧 {campo.get('nombre_campo', f'Campo {i+1}')} ({campo.get('tipo')})"):
                campo["nombre_campo"] = st.text_input(
                    "Nombre del campo (referencia)", value=campo.get("nombre_campo", f"Campo {i+1}"), key=f"pro_nombre_{i}"
                )
                tipos = ["texto", "parrafo", "qr"]
                campo["tipo"] = st.selectbox(
                    "Tipo de campo", tipos, index=tipos.index(campo.get("tipo", "texto")), key=f"pro_tipo_{i}"
                )
                campo["pagina"] = st.number_input(
                    "Página", min_value=1, max_value=num_paginas,
                    value=min(int(campo.get("pagina", 1)), num_paginas), key=f"pro_pagina_{i}"
                )

                pagina_idx = int(campo["pagina"]) - 1
                if paginas_img and 0 <= pagina_idx < len(paginas_img):
                    pdf_dims = paginas_dims[pagina_idx]
                    create_hover_image(
                        paginas_img[pagina_idx], key=f"pro_{i}", width=600,
                        title=f"Página {campo['pagina']} - {campo['nombre_campo']}", pdf_dims=pdf_dims
                    )

                col_x, col_y = st.columns(2)
                with col_x:
                    campo["x"] = st.number_input("Coordenada X", min_value=0, value=int(campo.get("x", 50)), key=f"pro_x_{i}")
                with col_y:
                    campo["y"] = st.number_input("Coordenada Y", min_value=0, value=int(campo.get("y", 50)), key=f"pro_y_{i}")

                if campo["tipo"] in ("texto", "parrafo"):
                    familias = ["Helvetica", "Times", "Courier"]
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        campo["font_familia"] = st.selectbox(
                            "Fuente", familias, index=familias.index(campo.get("font_familia", "Helvetica")), key=f"pro_font_{i}"
                        )
                    with col_f2:
                        campo["font_size"] = st.number_input(
                            "Tamaño", min_value=6, max_value=96, value=int(campo.get("font_size", 14)), key=f"pro_fontsize_{i}"
                        )
                    with col_f3:
                        campo["centrado"] = st.checkbox("Centrado", value=campo.get("centrado", False), key=f"pro_centrado_{i}")

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        campo["negrita"] = st.checkbox("Negrita", value=campo.get("negrita", False), key=f"pro_negrita_{i}")
                    with col_b2:
                        campo["cursiva"] = st.checkbox("Cursiva", value=campo.get("cursiva", False), key=f"pro_cursiva_{i}")

                if campo["tipo"] == "texto":
                    columnas = list(df_pro.columns)
                    idx_col = columnas.index(campo["columna_excel"]) if campo.get("columna_excel") in columnas else 0
                    campo["columna_excel"] = st.selectbox("Columna del Excel", columnas, index=idx_col, key=f"pro_col_{i}")
                    campo["formatear_nombre"] = st.checkbox(
                        "Formatear como nombre (mayúsculas)", value=campo.get("formatear_nombre", False), key=f"pro_formatnombre_{i}"
                    )
                    campo["usar_como_archivo"] = st.checkbox(
                        "Usar como nombre de archivo", value=campo.get("usar_como_archivo", False), key=f"pro_usararchivo_{i}"
                    )

                elif campo["tipo"] == "parrafo":
                    campo["plantilla_texto"] = st.text_area(
                        "Texto de la plantilla (usa {variable} y tus propios saltos de línea)",
                        value=campo.get("plantilla_texto", ""), height=150, key=f"pro_plantilla_{i}"
                    )
                    variables_detectadas = generador_pro.extraer_variables(campo["plantilla_texto"])
                    variables_map = campo.get("variables", {})
                    nuevas_variables = {}
                    if variables_detectadas:
                        st.caption("Variables detectadas — mapea cada una a una columna del Excel:")
                        columnas = list(df_pro.columns)
                        for var in variables_detectadas:
                            valor_actual = variables_map.get(var)
                            idx_col = columnas.index(valor_actual) if valor_actual in columnas else 0
                            nuevas_variables[var] = st.selectbox(f"{{{var}}} → columna", columnas, index=idx_col, key=f"pro_var_{i}_{var}")
                    campo["variables"] = nuevas_variables
                    campo["interlineado"] = st.number_input(
                        "Interlineado (pt)", min_value=6, max_value=96,
                        value=int(campo.get("interlineado", campo.get("font_size", 14) + 4)), key=f"pro_interlineado_{i}"
                    )

                elif campo["tipo"] == "qr":
                    columnas = list(df_pro.columns)
                    idx_col = columnas.index(campo["columna_url"]) if campo.get("columna_url") in columnas else 0
                    campo["columna_url"] = st.selectbox("Columna con la URL/dato del QR", columnas, index=idx_col, key=f"pro_qrcol_{i}")
                    col_qw, col_qh = st.columns(2)
                    with col_qw:
                        campo["ancho"] = st.number_input("Ancho QR (pt)", min_value=10, max_value=500, value=int(campo.get("ancho", 100)), key=f"pro_qrw_{i}")
                    with col_qh:
                        campo["alto"] = st.number_input("Alto QR (pt)", min_value=10, max_value=500, value=int(campo.get("alto", 100)), key=f"pro_qrh_{i}")

                if st.button("🗑️ Eliminar campo", key=f"pro_del_{i}"):
                    eliminar_idx = i

        if eliminar_idx is not None:
            campos.pop(eliminar_idx)
            st.rerun()

        st.download_button(
            "💾 Descargar plantilla (JSON)",
            data=json.dumps(campos, ensure_ascii=False, indent=2),
            file_name="plantilla_certificado.json",
            mime="application/json",
        )

        if st.button("🚀 Generar Certificados (Pro)"):
            resultados_pro = generador_pro.generar_certificados_pro(df_pro, pdf_base_file_pro, output_dir_pro, campos)
            st.success(f"✅ Generados {len(resultados_pro)} PDFs en: {output_dir_pro}")
            st.dataframe(resultados_pro)

# --- Generador de PDF Avanzado ---
elif opcion == "Generador de PDF Avanzado":
    st.header("🔹 Generador de PDF Avanzado")
    st.caption(
        "Igual que el Pro (texto, párrafo con variables y QR), pero con clic directo sobre el PDF "
        "para fijar coordenadas y un botón de vista previa con datos reales de la primera fila del Excel."
    )

    uploaded_file_adv = st.file_uploader("Sube Excel con los datos", type=["xlsx", "xlsm", "csv"], key="adv_excel")
    pdf_base_file_adv = st.file_uploader("Sube PDF base", type=["pdf"], key="adv_pdf")
    output_dir_adv = st.text_input("Carpeta de salida", key="adv_output_dir")

    st.session_state.setdefault("campos_avanzado", [])

    with st.expander("📂 Cargar plantilla guardada"):
        plantilla_file_adv = st.file_uploader("Archivo de plantilla (.json)", type=["json"], key="adv_plantilla_upload")
        if plantilla_file_adv and st.button("Aplicar plantilla cargada", key="adv_aplicar_plantilla"):
            try:
                st.session_state["campos_avanzado"] = json.load(plantilla_file_adv)
                st.success("Plantilla cargada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo leer la plantilla: {e}")

    if uploaded_file_adv and pdf_base_file_adv and output_dir_adv:
        if uploaded_file_adv.name.endswith(".csv"):
            df_adv = pd.read_csv(uploaded_file_adv, sep=";", dtype=str)
        else:
            df_adv = pd.read_excel(uploaded_file_adv, dtype=str, engine="openpyxl")

        pdf_bytes_adv = pdf_base_file_adv.getvalue()

        paginas_img_adv = []
        paginas_dims_adv = []
        try:
            paginas_img_adv = convert_from_bytes(pdf_bytes_adv, dpi=150, poppler_path=POPPLER_PATH)
            base_pdf_reader_adv = PdfReader(BytesIO(pdf_bytes_adv))
            paginas_dims_adv = [(float(p.mediabox.width), float(p.mediabox.height)) for p in base_pdf_reader_adv.pages]
        except Exception as e:
            st.error(f"No se pudo previsualizar el PDF: {e}")
            st.info(f"Verifica Poppler en: {POPPLER_PATH or 'PATH del sistema'} -> {os.path.exists(POPPLER_PATH) if POPPLER_PATH else 'revisar instalacion de poppler-utils'}")

        num_paginas_adv = max(len(paginas_img_adv), 1)

        st.subheader("🧩 Campos del certificado")
        if st.button("➕ Agregar campo", key="adv_agregar_campo"):
            primera_col = df_adv.columns[0] if len(df_adv.columns) else ""
            st.session_state["campos_avanzado"].append({
                "nombre_campo": f"Campo {len(st.session_state['campos_avanzado']) + 1}",
                "tipo": "texto",
                "pagina": 1,
                "x": 50, "y": 50,
                "centrado": False,
                "font_familia": "Helvetica",
                "font_size": 14,
                "negrita": False,
                "cursiva": False,
                "color": "#000000",
                "columna_excel": primera_col,
                "usar_como_archivo": False,
                "formatear_nombre": False,
                "plantilla_texto": "",
                "variables": {},
                "interlineado": 18,
                "columna_url": primera_col,
                "ancho": 100,
                "alto": 100,
            })
            st.rerun()

        campos_adv = st.session_state["campos_avanzado"]
        eliminar_idx_adv = None

        for i, campo in enumerate(campos_adv):
            with st.expander(f"🔧 {campo.get('nombre_campo', f'Campo {i+1}')} ({campo.get('tipo')})"):
                campo["nombre_campo"] = st.text_input(
                    "Nombre del campo (referencia)", value=campo.get("nombre_campo", f"Campo {i+1}"), key=f"adv_nombre_{i}"
                )
                tipos = ["texto", "parrafo", "qr"]
                campo["tipo"] = st.selectbox(
                    "Tipo de campo", tipos, index=tipos.index(campo.get("tipo", "texto")), key=f"adv_tipo_{i}"
                )
                campo["pagina"] = st.number_input(
                    "Página", min_value=1, max_value=num_paginas_adv,
                    value=min(int(campo.get("pagina", 1)), num_paginas_adv), key=f"adv_pagina_{i}"
                )

                pagina_idx = int(campo["pagina"]) - 1
                if paginas_img_adv and 0 <= pagina_idx < len(paginas_img_adv):
                    st.caption("👆 Haz clic sobre el punto exacto donde quieres ubicar el campo:")
                    click_key = f"adv_click_{i}"
                    click_value = streamlit_image_coordinates(
                        paginas_img_adv[pagina_idx], width=650, key=click_key
                    )
                    if click_value is not None:
                        last_click_key = f"adv_lastclick_{i}"
                        if st.session_state.get(last_click_key) != click_value.get("unix_time"):
                            st.session_state[last_click_key] = click_value.get("unix_time")
                            disp_w = click_value.get("width") or 1
                            disp_h = click_value.get("height") or 1
                            pdf_w, pdf_h = paginas_dims_adv[pagina_idx]
                            nuevo_x = round(click_value["x"] / disp_w * pdf_w)
                            nuevo_y = round(pdf_h - (click_value["y"] / disp_h * pdf_h))
                            st.session_state[f"adv_x_{i}"] = max(nuevo_x, 0)
                            st.session_state[f"adv_y_{i}"] = max(nuevo_y, 0)
                            campo["x"] = st.session_state[f"adv_x_{i}"]
                            campo["y"] = st.session_state[f"adv_y_{i}"]
                            st.rerun()

                col_x, col_y = st.columns(2)
                with col_x:
                    campo["x"] = st.number_input("Coordenada X", min_value=0, value=int(campo.get("x", 50)), key=f"adv_x_{i}")
                with col_y:
                    campo["y"] = st.number_input("Coordenada Y", min_value=0, value=int(campo.get("y", 50)), key=f"adv_y_{i}")

                if campo["tipo"] in ("texto", "parrafo"):
                    familias = ["Helvetica", "Times", "Courier"]
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        campo["font_familia"] = st.selectbox(
                            "Fuente", familias, index=familias.index(campo.get("font_familia", "Helvetica")), key=f"adv_font_{i}"
                        )
                    with col_f2:
                        campo["font_size"] = st.number_input(
                            "Tamaño", min_value=6, max_value=96, value=int(campo.get("font_size", 14)), key=f"adv_fontsize_{i}"
                        )
                    with col_f3:
                        campo["centrado"] = st.checkbox("Centrado", value=campo.get("centrado", False), key=f"adv_centrado_{i}")

                    col_b1, col_b2, col_b3 = st.columns(3)
                    with col_b1:
                        campo["negrita"] = st.checkbox("Negrita", value=campo.get("negrita", False), key=f"adv_negrita_{i}")
                    with col_b2:
                        campo["cursiva"] = st.checkbox("Cursiva", value=campo.get("cursiva", False), key=f"adv_cursiva_{i}")
                    with col_b3:
                        campo["color"] = st.color_picker("Color del texto", value=campo.get("color", "#000000"), key=f"adv_color_{i}")

                if campo["tipo"] == "texto":
                    columnas = list(df_adv.columns)
                    idx_col = columnas.index(campo["columna_excel"]) if campo.get("columna_excel") in columnas else 0
                    campo["columna_excel"] = st.selectbox("Columna del Excel", columnas, index=idx_col, key=f"adv_col_{i}")
                    campo["formatear_nombre"] = st.checkbox(
                        "Formatear como nombre (mayúsculas)", value=campo.get("formatear_nombre", False), key=f"adv_formatnombre_{i}"
                    )
                    campo["usar_como_archivo"] = st.checkbox(
                        "Usar como nombre de archivo", value=campo.get("usar_como_archivo", False), key=f"adv_usararchivo_{i}"
                    )

                elif campo["tipo"] == "parrafo":
                    campo["plantilla_texto"] = st.text_area(
                        "Texto de la plantilla (usa {variable} y tus propios saltos de línea)",
                        value=campo.get("plantilla_texto", ""), height=150, key=f"adv_plantilla_{i}"
                    )
                    variables_detectadas = generador_pro.extraer_variables(campo["plantilla_texto"])
                    variables_map = campo.get("variables", {})
                    nuevas_variables = {}
                    if variables_detectadas:
                        st.caption("Variables detectadas — mapea cada una a una columna del Excel:")
                        columnas = list(df_adv.columns)
                        for var in variables_detectadas:
                            valor_actual = variables_map.get(var)
                            idx_col = columnas.index(valor_actual) if valor_actual in columnas else 0
                            nuevas_variables[var] = st.selectbox(f"{{{var}}} → columna", columnas, index=idx_col, key=f"adv_var_{i}_{var}")
                    campo["variables"] = nuevas_variables
                    campo["interlineado"] = st.number_input(
                        "Interlineado (pt)", min_value=6, max_value=96,
                        value=int(campo.get("interlineado", campo.get("font_size", 14) + 4)), key=f"adv_interlineado_{i}"
                    )

                elif campo["tipo"] == "qr":
                    columnas = list(df_adv.columns)
                    idx_col = columnas.index(campo["columna_url"]) if campo.get("columna_url") in columnas else 0
                    campo["columna_url"] = st.selectbox("Columna con la URL/dato del QR", columnas, index=idx_col, key=f"adv_qrcol_{i}")
                    col_qw, col_qh, col_qc = st.columns(3)
                    with col_qw:
                        campo["ancho"] = st.number_input("Ancho QR (pt)", min_value=10, max_value=500, value=int(campo.get("ancho", 100)), key=f"adv_qrw_{i}")
                    with col_qh:
                        campo["alto"] = st.number_input("Alto QR (pt)", min_value=10, max_value=500, value=int(campo.get("alto", 100)), key=f"adv_qrh_{i}")
                    with col_qc:
                        campo["color"] = st.color_picker("Color del QR", value=campo.get("color", "#000000"), key=f"adv_qrcolor_{i}")
                        if campo["color"].upper() in ("#FFFFFF", "#FFF"):
                            st.warning("Un QR blanco sobre fondo blanco no se podrá escanear.")

                if st.button("🗑️ Eliminar campo", key=f"adv_del_{i}"):
                    eliminar_idx_adv = i

        if eliminar_idx_adv is not None:
            campos_adv.pop(eliminar_idx_adv)
            st.rerun()

        st.download_button(
            "💾 Descargar plantilla (JSON)",
            data=json.dumps(campos_adv, ensure_ascii=False, indent=2),
            file_name="plantilla_certificado_avanzado.json",
            mime="application/json",
            key="adv_descargar_plantilla",
        )

        st.subheader("🖨️ Vista previa de impresión")
        if st.button("🖨️ Vista previa de impresión", key="adv_vista_previa"):
            if len(df_adv) == 0:
                st.warning("El Excel no tiene filas para previsualizar.")
            else:
                try:
                    primera_fila = df_adv.iloc[0]
                    preview_bytes = generador_avanzado.generar_pdf_preview_bytes(primera_fila, pdf_base_file_adv, campos_adv)
                    preview_imgs = convert_from_bytes(preview_bytes, dpi=150, poppler_path=POPPLER_PATH)
                    for pnum, pimg in enumerate(preview_imgs, start=1):
                        st.image(pimg, caption=f"Página {pnum}", use_container_width=True)
                except Exception as e:
                    st.error(f"No se pudo generar la vista previa: {e}")

        if st.button("🚀 Generar Certificados", key="adv_generar"):
            resultados_adv = generador_pro.generar_certificados_pro(df_adv, pdf_base_file_adv, output_dir_adv, campos_adv)
            st.success(f"✅ Generados {len(resultados_adv)} PDFs en: {output_dir_adv}")
            st.dataframe(resultados_adv)

# --- Renombrador de PDFs ---
elif opcion == "Renombrador de PDFs":
    st.header("🔹 Renombrador de PDFs")
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx","xlsm","csv"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=";", dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str, engine="openpyxl")
        st.success("✅ Archivo cargado correctamente")
        st.dataframe(df.head())
        col_cedula = st.selectbox("Selecciona columna de Cédula", df.columns)
        validar_cedula = st.checkbox("Validar formato de cédula ecuatoriana (10 dígitos)", value=True)
        col_nombre = st.selectbox("Selecciona columna de Nombres", df.columns)
        validacion_avanzada = st.checkbox(
            "Validación avanzada de nombres (separa apellidos/nombres para nombres completos)",
            value=True,
            help="Desactívala si la columna de Nombres tiene valores cortos (1-2 palabras) o códigos: "
                 "en ese caso solo se normaliza y compara tal cual, sin invertir nada.",
        )
        columnas = list(df.columns)
        col_archivo = st.selectbox(
            "Columna a usar como nombre del PDF",
            columnas,
            index=columnas.index(col_cedula),
        )
        pdf_folder = st.text_input("Ruta de carpeta PDFs")
        if st.button("Procesar Renombrado"):
            if not pdf_folder or not Path(pdf_folder).exists():
                st.error("❌ Ruta inválida")
            else:
                df_resultados, df_limpio, df_problemas = renombrador.procesar_archivos(
                    df, col_cedula, col_nombre, pdf_folder,
                    validar_cedula=validar_cedula, col_archivo=col_archivo,
                    validacion_avanzada=validacion_avanzada,
                )
                st.success("✅ Proceso completado")
                st.subheader("📄 Resultados del Renombrado")
                st.dataframe(df_resultados)
                st.subheader("✅ Datos válidos tras limpieza")
                st.dataframe(df_limpio)
                st.subheader("❌ Casos problemáticos")
                st.dataframe(df_problemas)
                csv_output = df_resultados.to_csv(sep=";", index=False, encoding="utf-8-sig")
                st.download_button("⬇️ Descargar reporte CSV", data=csv_output, file_name="reporte_final.csv", mime="text/csv")

# --- Envio Masivo de Correos ---
elif opcion == "Envio Masivo de Correos":
    st.header("📧 Envío de Correos Masivo / Individual")
    
    modo = st.radio("Modo de envío", ["Masivo desde Excel", "Correo único"])
    
    # Logo seleccionable
    logo_file = st.file_uploader("Selecciona logo (opcional)", type=["png","jpg","jpeg"])
    
    # Asunto editable
    asunto = st.text_input("Asunto del correo", "Enviado desde ISTCUMANDA")
    
    # Pie de correo editable con valores por defecto
    pie_correo_default = """**ISTCUMANDA**
Correo: soporte@hotmail.com
Celular: 098395029
Dirección: Cumanda
Web: www.istcumanda.edu.ec"""
    pie_correo = st.text_area("Pie de correo (opcional)", pie_correo_default)
    
    # Cuerpo del mensaje (solo negrita y saltos de línea)
    cuerpo_default = "Estimado/a **{nombre}**, \n\nBienvenido/a a la plataforma virtual.\n\nUsuario: {usuario}\nContraseña: {contrasena}"
    cuerpo = st.text_area(
        "Cuerpo del mensaje (Markdown permitido: **negrita** y saltos de línea)", 
        cuerpo_default,
        height=200
    )

    # --- Convertir Markdown a HTML ---
    def markdown_to_html(text):
        # Solo convertir negrita y saltos de línea
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = text.replace('\n', '<br>')
        return text

    html_body = markdown_to_html(cuerpo)
    
    # --- Construir template HTML ---
    html_template = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            {html_body}
            <hr style="margin-top: 20px;">
            <p style="font-size: 12px; color: gray;">{markdown_to_html(pie_correo)}</p>
        </div>
    </body>
    </html>
    """

    # --- Modo Masivo ---
    if modo == "Masivo desde Excel":
        uploaded_file = st.file_uploader("Sube Excel con contactos", type=["xlsx","xlsm","csv"])
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, sep=";", dtype=str)
            else:
                df = pd.read_excel(uploaded_file, dtype=str, engine="openpyxl")
            st.dataframe(df.head())
            col_correo = st.selectbox("Columna con Correos", df.columns)
            col_nombre = st.selectbox("Columna con Nombres", df.columns)
            col_cargo = st.selectbox("Columna con Cargo (opcional)", [None] + list(df.columns))
            
            if st.button("Enviar correos masivos"):
                df_resultados = correos.enviar_correos(df, col_correo, col_nombre, col_cargo,
                                                       html_template=html_template, logo_file=logo_file, asunto=asunto)
                st.success("✅ Correos enviados")
                st.dataframe(df_resultados)

    # --- Modo Individual ---
    else:
        correo = st.text_input("Correo del destinatario")
        nombre = st.text_input("Nombre del destinatario")
        cargo = st.text_input("Cargo (opcional)")
        usuario = st.text_input("Usuario (opcional)")
        contrasena = st.text_input("Contraseña (opcional)")
        
        if st.button("Enviar correo único"):
            if correo.strip() == "":
                st.error("❌ Ingresa un correo válido")
            else:
                df_temp = pd.DataFrame([{
                    "correo": correo,
                    "nombre": nombre,
                    "cargo": cargo,
                    "usuario": usuario,
                    "contrasena": contrasena
                }])
                df_resultados = correos.enviar_correos(df_temp, "correo", "nombre", "cargo",
                                                       html_template=html_template, logo_file=logo_file, asunto=asunto)
                st.success("✅ Correo enviado")
                st.dataframe(df_resultados)

# --- 🔹 NUEVA SECCIÓN: Envio Masivo de WhatsApp ---
elif opcion == "Envio Masivo de WhatsApp":
    st.header("💬 Envío Masivo de WhatsApp")
    st.markdown("""
    Esta herramienta te permite enviar mensajes personalizados de WhatsApp a múltiples contactos.
    
    **Características:**
    - ✅ Envío personalizado con nombre y apellido
    - ✅ Adjuntar imagen o PDF (opcional)
    - ✅ Control de velocidad entre mensajes
    - ✅ Reporte detallado de envíos
    """)
    
    # Importar módulo de WhatsApp
    try:
        #from .funciones import whatsapp
        #from funciones.generador import generar_certificados
        from funciones import whatsapp
    except ImportError:
        st.error("❌ No se pudo importar el módulo de WhatsApp. Asegúrate de tener instalado Selenium.")
        st.code("pip install selenium", language="bash")
        st.stop()
    
    # --- Cargar Excel ---
    st.subheader("📁 1. Cargar contactos")
    uploaded_file = st.file_uploader("Sube Excel con contactos", type=["xlsx","xlsm","csv"], key="whatsapp_excel")
    
    if uploaded_file:
        # Leer archivo
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=";", dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str, engine="openpyxl")
        
        st.success("✅ Archivo cargado correctamente")
        st.dataframe(df.head())
        
        # --- Mapear columnas ---
        st.subheader("🔗 2. Mapear columnas")
        col1, col2, col3 = st.columns(3)
        with col1:
            col_numero = st.selectbox("Columna con Teléfonos", df.columns, key="col_numero")
        with col2:
            col_nombre = st.selectbox("Columna con Nombres (opcional)", [""] + list(df.columns), key="col_nombre_wa")
        with col3:
            col_apellido = st.selectbox("Columna con Apellidos (opcional)", [""] + list(df.columns), key="col_apellido_wa")
        
        # Validar números
        df_validos, df_invalidos = whatsapp.procesar_excel_whatsapp(df, col_numero)
        
        st.info(f"📊 **Total contactos:** {len(df)} | ✅ **Válidos:** {len(df_validos)} | ❌ **Inválidos:** {len(df_invalidos)}")
        
        if len(df_invalidos) > 0:
            with st.expander("⚠️ Ver números inválidos"):
                st.dataframe(df_invalidos[[col_numero]])
        
        # --- Configurar mensaje ---
        st.subheader("📝 3. Configurar mensaje")
        st.info("""
        **Variables disponibles:**
        - `{nombre}` - Se reemplaza con el nombre
        - `{apellido}` - Se reemplaza con el apellido
        - `{nombre_completo}` - Nombre + Apellido
        """)
        
        mensaje_default = """Hola {nombre} {apellido},

Te saluda el equipo de ISTCUMANDA.

Te enviamos este mensaje para recordarte...

Saludos cordiales."""
        
        mensaje = st.text_area(
            "Escribe tu mensaje",
            mensaje_default,
            height=200,
            key="mensaje_wa"
        )
        
        # --- Archivo adjunto opcional ---
        st.subheader("📎 4. Archivo adjunto (opcional)")
        archivo_adjunto = st.file_uploader(
            "Adjuntar imagen o PDF (opcional)",
            type=["png", "jpg", "jpeg", "pdf"],
            key="adjunto_wa"
        )
        
        ruta_adjunto = None
        if archivo_adjunto:
            # Guardar temporalmente
            ruta_adjunto = Path("temp_adjuntos") / archivo_adjunto.name
            ruta_adjunto.parent.mkdir(exist_ok=True)
            with open(ruta_adjunto, "wb") as f:
                f.write(archivo_adjunto.read())
            st.success(f"✅ Archivo cargado: {archivo_adjunto.name}")
        
        # --- Configuración de envío ---
        st.subheader("⚙️ 5. Configuración de envío")
        st.caption(
            "Para lotes grandes (150-200 contactos/día), un delay aleatorio y pausas largas "
            "cada cierto número de mensajes reducen el riesgo de bloqueo por WhatsApp."
        )
        delay_min, delay_max = st.slider(
            "Rango de espera aleatoria entre mensajes (segundos)",
            min_value=5,
            max_value=60,
            value=(15, 30),
            help="Se espera un tiempo aleatorio dentro de este rango tras cada mensaje, en vez de un tiempo fijo."
        )

        col_pausa1, col_pausa2 = st.columns(2)
        with col_pausa1:
            submensajes_pausa = st.number_input(
                "Pausa larga cada cuántos mensajes",
                min_value=0,
                max_value=200,
                value=35,
                help="0 = desactivar. Recomendado: cada 30-40 mensajes."
            )
        with col_pausa2:
            pausa_min, pausa_max = st.slider(
                "Duración de la pausa larga (minutos)",
                min_value=1,
                max_value=30,
                value=(5, 10)
            )
        
        # --- Vista previa del mensaje ---
        with st.expander("👁️ Vista previa del mensaje"):
            if len(df_validos) > 0:
                ejemplo = df_validos.iloc[0]
                nombre_ej = ejemplo.get(col_nombre, 'Juan') if col_nombre else 'Juan'
                apellido_ej = ejemplo.get(col_apellido, 'Pérez') if col_apellido else 'Pérez'
                
                mensaje_preview = mensaje.replace('{nombre}', str(nombre_ej))
                mensaje_preview = mensaje_preview.replace('{apellido}', str(apellido_ej))
                mensaje_preview = mensaje_preview.replace('{nombre_completo}', f"{nombre_ej} {apellido_ej}".strip())
                
                st.text_area("Así se verá el mensaje:", mensaje_preview, height=150, disabled=True)
        
        # --- Botón de envío ---
        st.subheader("🚀 6. Iniciar envío")
        
        st.warning("""
        **⚠️ IMPORTANTE:**
        1. Se abrirá WhatsApp Web en tu navegador
        2. Escanea el código QR con tu teléfono
        3. Espera a que se cargue completamente
        4. Los mensajes se enviarán automáticamente
        5. NO cierres la ventana del navegador durante el proceso
        """)
        
        if st.button("📲 Iniciar envío de WhatsApp", type="primary"):
            if len(df_validos) == 0:
                st.error("❌ No hay números válidos para enviar")
            else:
                # Crear bot
                bot = whatsapp.WhatsAppBot(
                    delay_min=delay_min,
                    delay_max=delay_max,
                    submensajes_pausa=submensajes_pausa,
                    pausa_min_minutos=pausa_min,
                    pausa_max_minutos=pausa_max,
                )
                
                # Contenedor de progreso
                status_placeholder = st.empty()
                progreso_bar = st.progress(0)
                resultado_placeholder = st.empty()
                
                try:
                    # Iniciar navegador
                    status_placeholder.info("🌐 Abriendo WhatsApp Web...")
                    bot.iniciar_navegador()
                    
                    # Esperar login
                    status_placeholder.warning("📱 Por favor, escanea el código QR en la ventana del navegador")
                    if bot.esperar_login(timeout=90):
                        status_placeholder.success("✅ Login exitoso. Iniciando envío...")
                        
                        # Callback para actualizar progreso
                        def actualizar_progreso(actual, total, resultado):
                            progreso = actual / total
                            progreso_bar.progress(progreso)
                            
                            emoji = "✅" if resultado['status'] == 'enviado' else "❌"
                            status_placeholder.info(
                                f"{emoji} Enviando {actual}/{total}: {resultado['numero']} - {resultado['status']}"
                            )

                        # Callback para avisar de la pausa larga
                        def avisar_pausa(segundos_pausa):
                            status_placeholder.warning(
                                f"⏸️ Pausa larga anti-bloqueo: esperando ~{segundos_pausa/60:.1f} minutos..."
                            )

                        # Enviar mensajes
                        df_resultados = bot.enviar_mensajes_masivos(
                            df_validos,
                            col_numero,
                            col_nombre if col_nombre else None,
                            col_apellido if col_apellido else None,
                            mensaje,
                            archivo_adjunto=str(ruta_adjunto) if ruta_adjunto else None,
                            callback_progreso=actualizar_progreso,
                            callback_pausa=avisar_pausa
                        )
                        
                        # Mostrar resultados
                        status_placeholder.success("🎉 ¡Envío completado!")
                        
                        enviados = len(df_resultados[df_resultados['status'] == 'enviado'])
                        fallidos = len(df_resultados[df_resultados['status'] == 'error'])
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("📊 Total", len(df_resultados))
                        col2.metric("✅ Enviados", enviados)
                        col3.metric("❌ Fallidos", fallidos)
                        
                        st.subheader("📋 Reporte detallado")
                        st.dataframe(df_resultados)
                        
                        # Descargar reporte
                        csv_reporte = df_resultados.to_csv(sep=";", index=False, encoding="utf-8-sig")
                        st.download_button(
                            "⬇️ Descargar reporte CSV",
                            data=csv_reporte,
                            file_name="reporte_whatsapp.csv",
                            mime="text/csv"
                        )
                    else:
                        status_placeholder.error("❌ Tiempo de espera agotado. No se pudo completar el login.")
                
                except Exception as e:
                    st.error(f"❌ Error durante el proceso: {str(e)}")
                
                finally:
                    # Cerrar navegador
                    bot.cerrar()
                    
                    # Limpiar archivo temporal
                    if ruta_adjunto and ruta_adjunto.exists():
                        ruta_adjunto.unlink()

# --- Generador CSV Moodle ---
elif opcion == "Generador CSV Moodle":
    st.header("📊 Generador de CSV para Moodle")

    # =============================
    # Funciones de validación
    # =============================

    def cedula_valida_ecuador(cedula: str) -> bool:
        """
        Valida una cédula ecuatoriana usando el algoritmo oficial.
        """
        if not cedula or not cedula.isdigit() or len(cedula) != 10:
            return False

        provincia = int(cedula[0:2])
        if provincia < 1 or (provincia > 24 and provincia != 30):
            return False

        tercer_digito = int(cedula[2])
        if tercer_digito > 5:  # personas naturales (0-5)
            return False

        coeficientes = [2,1,2,1,2,1,2,1,2]  # posiciones 1 a 9
        suma = 0
        for i in range(9):
            val = int(cedula[i]) * coeficientes[i]
            if val > 9:
                val -= 9
            suma += val

        digito_verificador = (10 - (suma % 10)) % 10
        return digito_verificador == int(cedula[9])

    def validar_cedula(cedula: str) -> str:
        if pd.isna(cedula):
            return ""
        cedula = str(cedula).strip()
        return cedula if cedula_valida_ecuador(cedula) else ""

    def validar_telefono(telefono: str) -> str:
        if pd.isna(telefono) or not str(telefono).strip():
            return "0999999999"
        telefono = str(telefono).strip()
        return telefono if re.fullmatch(r"\d{10}", telefono) else "0999999999"

    def validar_correo(correo: str) -> str:
        if pd.isna(correo):
            return ""
        correo = str(correo).strip().lower()
        return correo if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", correo) else ""

    # =============================
    # Cargar archivo maestro
    # =============================
    uploaded_moodle = st.file_uploader("📂 Sube Excel de alumnos", type=["xlsx","xlsm","csv"])
    RUTA_MAESTRO = Path("EC_MAESTRO_DIPLOMADOS.xlsx")
    if not RUTA_MAESTRO.exists():
        st.error("⚠️ No se encontró el archivo maestro en la raíz del proyecto (EC_MAESTRO_DIPLOMADOS.xlsx)")
    else:
        df_cursos = pd.read_excel(RUTA_MAESTRO, dtype=str, engine="openpyxl")

        if uploaded_moodle:
            if uploaded_moodle.name.endswith(".csv"):
                df = pd.read_csv(uploaded_moodle, sep=";", dtype=str)
            else:
                df = pd.read_excel(uploaded_moodle, dtype=str, engine="openpyxl")

            st.subheader("📄 Vista previa de tus datos")
            st.dataframe(df.head())

            curso_seleccionado = st.selectbox("📘 Selecciona un curso", df_cursos['CURSO'].unique())
            modulos = df_cursos[df_cursos['CURSO'] == curso_seleccionado]
            st.write("📚 Módulos seleccionados:")
            st.dataframe(modulos)

            # =============================
            # Mapear columnas
            # =============================
            st.subheader("🔗 Mapear columnas de tu Excel")
            col_username = st.selectbox("Columna para username (CEDULA)", [""] + list(df.columns))
            col_firstname = st.selectbox("Columna para firstname", [""] + list(df.columns))
            col_lastname = st.selectbox("Columna para lastname", [""] + list(df.columns))
            col_email = st.selectbox("Columna para email", [""] + list(df.columns))
            col_phone = st.selectbox("Columna para phone1", [""] + list(df.columns))
            col_description = st.selectbox("Columna para description", [""] + list(df.columns))
            col_password = st.selectbox("Columna para password", [""] + list(df.columns))
            col_cohort = st.selectbox("Columna para cohort1", [""] + list(df.columns))  # 🔹 NUEVO

            # Fecha actual como valor por defecto
            fecha_default = pd.Timestamp.today().strftime("%Y-%m-%d")
            fecha_manual = st.text_input("📅 Fecha de inscripción (ej: 2025-09-07)", value=fecha_default)

            # =============================
            # Procesar y generar CSV
            # =============================
            if st.button("🚀 Generar CSV"):
                errores = []
                df_final = pd.DataFrame()
                df_errores = pd.DataFrame()  # Reporte de errores

                if col_username:
                    df_final['username'] = df[col_username].apply(validar_cedula)
                    df_final['idnumber'] = df_final['username']

                    # Guardar filas con cedulas inválidas
                    df_invalidas = df[df[col_username].apply(lambda x: not cedula_valida_ecuador(str(x).strip()) if pd.notna(x) else True)]
                    if not df_invalidas.empty:
                        df_errores = pd.concat([df_errores, df_invalidas])
                        errores.append(f"❌ Se encontraron {len(df_invalidas)} cédulas inválidas.")

                if col_firstname:
                    df_final['firstname'] = df[col_firstname].astype(str).str.strip().str.upper()
                if col_lastname:
                    df_final['lastname'] = df[col_lastname].astype(str).str.strip().str.upper()
                if col_email:
                    df_final['email'] = df[col_email].apply(validar_correo)
                if col_phone:
                    df_final['phone1'] = df[col_phone].apply(validar_telefono)
                if col_description:
                    df_final['description'] = df[col_description].astype(str).str.strip().str.upper()
                if col_password:
                    df_final['password'] = df[col_password].astype(str).str.strip()
                if col_cohort:
                    df_final['cohort1'] = df[col_cohort].astype(str).str.strip().str.upper()
                else:
                    df_final['cohort1'] = ""  # 🔹 vacío si no se selecciona

                # Campos fijos
                df_final['enroltimestart1'] = fecha_manual
                df_final['role1'] = 'student'

                # Cursos dinámicos desde maestro
                for i, row in enumerate(modulos.itertuples(), start=1):
                    df_final[f'course{i}'] = row.NOMBRE_CORTO

                # Validaciones adicionales
                if 'email' in df_final and (df_final['email'] == "").any():
                    errores.append("❌ Hay correos inválidos (formato incorrecto).")

                if errores:
                    st.error("⚠️ Se encontraron problemas en los datos:")
                    for err in errores:
                        st.write(err)
                    st.dataframe(df_final)

                    # Mostrar reporte de cédulas inválidas
                    if not df_errores.empty:
                        st.subheader("📌 Reporte de cédulas inválidas")
                        st.dataframe(df_errores)
                        csv_reporte = df_errores.to_csv(sep=";", index=False, encoding="utf-8-sig")
                        st.download_button("⬇️ Descargar Reporte de Errores", data=csv_reporte, file_name="REPORTE_CEDULAS_INVALIDAS.csv", mime="text/csv")
                else:
                    siglas = modulos['SIGLAS'].iloc[0]
                    fecha_hoy = pd.Timestamp.today().strftime("%Y-%m-%d")
                    file_name = f"{fecha_hoy}_{siglas}_MATRICULA.csv"
                    csv_output = df_final.to_csv(sep=";", index=False, encoding="utf-8-sig")
                    st.success(f"✅ CSV generado: {file_name}")
                    st.download_button("⬇️ Descargar CSV", data=csv_output, file_name=file_name, mime="text/csv")