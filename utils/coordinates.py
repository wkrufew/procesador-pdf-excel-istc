import streamlit as st
import base64
from io import BytesIO

def image_to_base64(image):
    """Convierte imagen PIL a base64"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def create_hover_image(image, key, width=600, title="Imagen", pdf_dims=(842, 595)):
    """Crea una imagen con coordenadas ajustadas a la escala real del PDF"""
    img_b64 = image_to_base64(image)

    pdf_width, pdf_height = pdf_dims
    
    # Medidas de la imagen renderizada
    original_width, original_height = image.size
    scale_factor = width / original_width
    scaled_height = int(original_height * scale_factor)

    html_code = f"""
    <div style="position: relative; display: inline-block; margin: 10px 0;">
        <div style="margin-bottom: 10px; font-weight: bold; color: #333;">
            {title}
        </div>
        <div style="position: relative; display: inline-block; border: 2px solid #ddd; border-radius: 8px; overflow: hidden;">
            <img id="hover-img-{key}" 
                 src="data:image/png;base64,{img_b64}" 
                 style="width: {width}px; height: {scaled_height}px; display: block;"
                 onmousemove="showCoords(event, '{key}', {pdf_width}, {pdf_height})"
                 onmouseleave="hideCoords('{key}')"
            />
            <div id="coords-overlay-{key}" 
                 style="position: absolute; top: 10px; left: 10px; background: rgba(0, 0, 0, 0.8); 
                        color: white; padding: 8px 12px; border-radius: 4px; 
                        font-family: monospace; font-size: 14px; display: none; pointer-events: none; z-index: 1000;">
                X: 0, Y: 0
            </div>
            <div id="crosshair-{key}" style="position: absolute; pointer-events: none; z-index: 999; display: none;">
                <div style="position: absolute; width: 1px; height: {scaled_height}px; background: red; opacity: 0.6;"></div>
                <div style="position: absolute; width: {width}px; height: 1px; background: red; opacity: 0.6;"></div>
            </div>
        </div>
        <div style="margin-top: 10px; padding: 10px; background: #f0f8ff; border-radius: 4px; border-left: 4px solid #007acc;">
            <strong>💡 Instrucciones:</strong><br>
            • Mueve el mouse sobre la imagen para ver las coordenadas<br>
            • Las coordenadas se muestran en tiempo real ajustadas al tamaño real del PDF<br>
            • Ejemplo esperado: Nombre (421,310), Nota (708,64)<br>
        </div>
        <div id="current-coords-{key}" style="margin-top: 10px; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; color: #333;">
            <strong>Coordenadas actuales:</strong> Mueve el mouse sobre la imagen
        </div>
    </div>

    <style>
    #hover-img-{key} {{
        cursor: crosshair;
        transition: filter 0.2s ease;
    }}
    #hover-img-{key}:hover {{
        filter: brightness(1.1);
    }}
    </style>

    <script>
    function showCoords(event, key, pdfWidth, pdfHeight) {{
        const rect = event.target.getBoundingClientRect();
        const x_img = event.clientX - rect.left;
        const y_img = event.clientY - rect.top;

        // Convertir coordenadas de la imagen a escala del PDF
        const x_pdf = Math.round((x_img / rect.width) * pdfWidth);
        const y_pdf = Math.round(pdfHeight - (y_img / rect.height) * pdfHeight);

        // Overlay
        const overlay = document.getElementById('coords-overlay-' + key);
        overlay.innerHTML = `X: ${{x_pdf}}, Y: ${{y_pdf}}`;
        overlay.style.display = 'block';

        // Texto de coordenadas actuales
        const currentCoords = document.getElementById('current-coords-' + key);
        currentCoords.innerHTML = `<strong>Coordenadas actuales:</strong> X = ${{x_pdf}}, Y = ${{y_pdf}} 
                                  <small style="color: #666;">(PDF: ${{pdfWidth}}x${{pdfHeight}})</small>`;

        // Crosshair
        const crosshair = document.getElementById('crosshair-' + key);
        crosshair.style.display = 'block';
        crosshair.style.left = x_img + 'px';
        crosshair.style.top = y_img + 'px';
    }}

    function hideCoords(key) {{
        document.getElementById('coords-overlay-' + key).style.display = 'none';
        document.getElementById('crosshair-' + key).style.display = 'none';
        document.getElementById('current-coords-' + key).innerHTML = 
            '<strong>Coordenadas actuales:</strong> Mueve el mouse sobre la imagen';
    }}
    </script>
    """

    return st.components.v1.html(html_code, height=scaled_height + 150)

def mostrar_captura_coordenadas(page1_img, page2_img=None, col_nota=None, orientation="HORIZONTAL"):
    """Función para mostrar las imágenes con captura de coordenadas por hover"""
    pdf_dims = (842, 595) if orientation == "HORIZONTAL" else (595, 842)

    st.subheader("📍 Captura coordenadas con hover del mouse")
    st.info(f"✨ Mueve el mouse sobre las imágenes para ver las coordenadas en tiempo real (PDF: {pdf_dims[0]}x{pdf_dims[1]})")

    # Página 1 (Nombre)
    st.write("### 📄 Página 1: Ubicación del NOMBRE")
    create_hover_image(page1_img, "page1", width=700, title="Página 1 - Posición del Nombre", pdf_dims=pdf_dims)

    col1, col2 = st.columns(2)
    with col1:
        x_nombre = st.number_input("🎯 Coordenada X del Nombre", min_value=0, value=st.session_state.get('coords_nombre', (421, 310))[0], help="Posición horizontal (0=izquierda)")
    with col2:
        y_nombre = st.number_input("🎯 Coordenada Y del Nombre", min_value=0, value=st.session_state.get('coords_nombre', (421, 310))[1], help="Posición vertical (0=abajo)")
    
    if st.button("✅ Confirmar coordenadas del Nombre"):
        st.session_state.coords_nombre = (x_nombre, y_nombre)
        st.success(f"Coordenadas del nombre actualizadas: ({x_nombre}, {y_nombre})")

    # Página 2 (Nota)
    coords_nota = (None, None)
    if col_nota and page2_img:
        st.write("### 📄 Página 2: Ubicación de la NOTA")
        create_hover_image(page2_img, "page2", width=700, title="Página 2 - Posición de la Nota", pdf_dims=pdf_dims)

        col3, col4 = st.columns(2)
        with col3:
            x_nota = st.number_input("🎯 Coordenada X de la Nota", min_value=0, value=st.session_state.get('coords_nota', (708, 64))[0], help="Posición horizontal (0=izquierda)")
        with col4:
            y_nota = st.number_input("🎯 Coordenada Y de la Nota", min_value=0, value=st.session_state.get('coords_nota', (708, 64))[1], help="Posición vertical (0=abajo)")

        if st.button("✅ Confirmar coordenadas de la Nota"):
            st.session_state.coords_nota = (x_nota, y_nota)
            st.success(f"Coordenadas de la nota actualizadas: ({x_nota}, {y_nota})")
        coords_nota = (x_nota, y_nota)

    return (x_nombre, y_nombre), coords_nota
