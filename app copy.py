import re
import streamlit as st
import pandas as pd
from pathlib import Path
from funciones.generador import generar_certificados
from funciones import renombrador, correos
from utils.coordinates import mostrar_captura_coordenadas
from pdf2image import convert_from_bytes
import os
import markdown
import base64

# Configurar la ruta de Poppler
POPPLER_PATH = r'C:\poppler\Library\bin'

# Configuración inicial
st.set_page_config(page_title="ISTCUMANDA", page_icon="📘", layout="centered")
st.title("📘 Herramientas ISTCUMANDA")

# --- Menú lateral ---
opcion = st.sidebar.radio("Selecciona opción", [
    "Inicio",
    "Generador de Certificados",
    "Renombrador de PDFs",
    "Envio Masivo de Correos",
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
            coords_nombre, coords_nota = mostrar_captura_coordenadas(page1_img, page2_img, col_nota)
        except Exception as e:
            st.error(f"No se pudo previsualizar PDF: {e}")
            st.info(f"Verifica Poppler en: {POPPLER_PATH} -> {os.path.exists(POPPLER_PATH)}")
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
        col_nombre = st.selectbox("Selecciona columna de Nombres", df.columns)
        pdf_folder = st.text_input("Ruta de carpeta PDFs")
        if st.button("Procesar Renombrado"):
            if not pdf_folder or not Path(pdf_folder).exists():
                st.error("❌ Ruta inválida")
            else:
                df_resultados, df_limpio, df_problemas = renombrador.procesar_archivos(df, col_cedula, col_nombre, pdf_folder)
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
    
    html_template = markdown.markdown(cuerpo)
    
    # Insertar logo centrado si existe
    logo_html = ""
    if logo_file:
        
        logo_bytes = logo_file.read()
        logo_base64 = base64.b64encode(logo_bytes).decode()
        logo_html = f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_base64}" width="200"></div><br>'
    
    # Pie de correo en HTML
    pie_html = markdown.markdown(pie_correo.replace("\n", "<br>"))
    
    html_template = logo_html + html_template + "<br><br>" + pie_html

    if modo == "Masivo desde Excel":
        uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx","xlsm","csv"])
        
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, sep=";", dtype=str)
            else:
                df = pd.read_excel(uploaded_file, dtype=str, engine="openpyxl")
            
            col_correo = st.selectbox("Columna de correos", df.columns)
            col_nombre = st.selectbox("Columna de nombres (opcional)", [None] + list(df.columns))
            col_cargo = st.selectbox("Columna de cargo (opcional)", [None] + list(df.columns))
            
            if st.button("Enviar correos masivos"):
                df_resultados = correos.enviar_correos(df, col_correo, col_nombre, col_cargo,
                                                       html_template, logo_file, pie_correo, asunto)
                st.success("✅ Correos enviados")
                st.dataframe(df_resultados)

    else:  # Un solo destinatario
        correo = st.text_input("Correo destinatario")
        nombre = st.text_input("Nombre (opcional)")
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
                                                       html_template, logo_file, pie_correo, asunto)
                st.success("✅ Correo enviado")
                st.dataframe(df_resultados)

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

