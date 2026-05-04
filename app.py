import re
import streamlit as st
import pandas as pd
from pathlib import Path
from funciones.generador import generar_certificados
from funciones import renombrador, correos
from utils.coordinates import mostrar_captura_coordenadas
from pdf2image import convert_from_bytes
import os

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
        delay = st.slider(
            "Segundos de espera entre mensajes (recomendado: 8-15)",
            min_value=5,
            max_value=30,
            value=10,
            help="Mayor tiempo = menor riesgo de bloqueo por WhatsApp"
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
                bot = whatsapp.WhatsAppBot(delay_entre_mensajes=delay)
                
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
                        
                        # Enviar mensajes
                        df_resultados = bot.enviar_mensajes_masivos(
                            df_validos,
                            col_numero,
                            col_nombre if col_nombre else None,
                            col_apellido if col_apellido else None,
                            mensaje,
                            archivo_adjunto=str(ruta_adjunto) if ruta_adjunto else None,
                            callback_progreso=actualizar_progreso
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