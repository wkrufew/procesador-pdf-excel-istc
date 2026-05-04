# 🚀 Guía de Instalación - Envío Masivo de WhatsApp

## 📋 Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de ChromeDriver](#instalación-de-chromedriver)
3. [Instalación de Dependencias Python](#instalación-de-dependencias-python)
4. [Integración al Proyecto](#integración-al-proyecto)
5. [Preparación del Excel](#preparación-del-excel)
6. [Uso de la Aplicación](#uso-de-la-aplicación)
7. [Solución de Problemas](#solución-de-problemas)

---

## 1️⃣ Requisitos Previos

Antes de comenzar, asegúrate de tener:
- ✅ Python 3.8 o superior instalado
- ✅ Google Chrome instalado (última versión)
- ✅ WhatsApp instalado en tu teléfono
- ✅ Conexión a Internet estable
- ✅ Tu proyecto ISTCUMANDA funcionando

---

## 2️⃣ Instalación de ChromeDriver

### Opción A: Instalación Automática (Recomendada)

ChromeDriver se instalará automáticamente al ejecutar el código gracias a `webdriver-manager`. No necesitas hacer nada adicional.

### Opción B: Instalación Manual (Si la Opción A falla)

1. **Verificar versión de Chrome:**
   - Abre Chrome
   - Ve a `chrome://settings/help`
   - Anota tu versión (ej: 120.0.6099.109)

2. **Descargar ChromeDriver:**
   - Visita: https://googlechromelabs.github.io/chrome-for-testing/
   - Descarga la versión que coincida con tu Chrome
   - Para Windows: `chromedriver-win64.zip`

3. **Instalar ChromeDriver:**
   
   **Windows:**
   ```bash
   # Descomprime el archivo
   # Copia chromedriver.exe a: C:\Windows\System32\
   # O agrega la carpeta al PATH
   ```

   **Linux/Mac:**
   ```bash
   # Descomprime el archivo
   sudo mv chromedriver /usr/local/bin/
   sudo chmod +x /usr/local/bin/chromedriver
   ```

4. **Verificar instalación:**
   ```bash
   chromedriver --version
   ```

---

## 3️⃣ Instalación de Dependencias Python

### Paso 1: Activar tu entorno virtual

```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Paso 2: Instalar dependencias nuevas

```bash
pip install selenium webdriver-manager
```

O instalar todo desde el archivo requirements.txt actualizado:

```bash
pip install -r requirements.txt
```

### Paso 3: Verificar instalación

```python
python -c "import selenium; print(selenium.__version__)"
```

Deberías ver algo como: `4.16.0` o superior

---

## 4️⃣ Integración al Proyecto

### Estructura de archivos necesaria:

```
tu_proyecto/
│
├── app.py                          # ← Reemplazar con app_actualizado.py
├── funciones/
│   ├── __init__.py
│   ├── generador.py
│   ├── renombrador.py
│   ├── correos.py
│   └── whatsapp.py                 # ← NUEVO archivo
│
├── utils/
│   └── coordinates.py
│
├── assets/
│   └── logo.png
│
├── venv/                           # Tu entorno virtual
├── requirements.txt                # ← Actualizado
└── README.md
```

### Pasos de integración:

**Paso 1:** Copia el archivo `whatsapp.py` a tu carpeta `funciones/`

```bash
# Desde donde descargaste los archivos
copy whatsapp.py tu_proyecto/funciones/
```

**Paso 2:** Reemplaza tu `app.py` actual

```bash
# Haz backup de tu app.py actual
copy app.py app_backup.py

# Reemplaza con la versión actualizada
copy app_actualizado.py app.py
```

**Paso 3:** Actualiza tu archivo `requirements.txt`

Agrega estas líneas al final:

```txt
selenium>=4.16.0
webdriver-manager>=4.0.1
```

---

## 5️⃣ Preparación del Excel

### Formato del Excel requerido:

Tu archivo Excel debe tener **al menos** estas columnas:

| Nombre    | Apellido  | Teléfono      |
|-----------|-----------|---------------|
| Juan      | Pérez     | 0987654321    |
| María     | González  | 0991234567    |
| Pedro     | Ramírez   | +593998765432 |

### Formatos de teléfono aceptados:

✅ **Válidos:**
- `0987654321` (10 dígitos comenzando en 09)
- `593987654321` (código país sin +)
- `+593987654321` (código país con +)

❌ **Inválidos:**
- `98765432` (muy corto)
- `02123456` (teléfono fijo)
- `0887654321` (no comienza con 09)

### Consejos:
- Asegúrate de que los números no tengan espacios ni guiones
- Verifica que todos sean números celulares (comienzan con 09)
- Los nombres y apellidos son opcionales pero recomendados

---

## 6️⃣ Uso de la Aplicación

### Paso a paso:

**1. Ejecutar la aplicación:**

```bash
streamlit run app.py
```

**2. En el navegador:**
- Ve al menú lateral
- Selecciona: **"Envio Masivo de WhatsApp"**

**3. Cargar contactos:**
- Sube tu archivo Excel
- La app validará automáticamente los números
- Te mostrará cuántos son válidos

**4. Mapear columnas:**
- Selecciona qué columna tiene los teléfonos
- Selecciona columnas de nombre/apellido (opcionales)

**5. Configurar mensaje:**
- Escribe tu mensaje
- Usa variables: `{nombre}`, `{apellido}`, `{nombre_completo}`
- Ejemplo: "Hola {nombre}, te recordamos que..."

**6. Adjuntar archivo (opcional):**
- Sube una imagen (PNG, JPG) o PDF
- Se enviará junto con el mensaje

**7. Configurar velocidad:**
- Ajusta el delay entre mensajes (recomendado: 10 segundos)
- Más tiempo = menos riesgo de bloqueo

**8. Iniciar envío:**
- Haz clic en "📲 Iniciar envío de WhatsApp"
- Se abrirá WhatsApp Web en una ventana nueva
- **IMPORTANTE:** Escanea el código QR con tu teléfono
- Los mensajes se enviarán automáticamente

**9. Esperar y supervisar:**
- Verás el progreso en tiempo real
- NO cierres la ventana del navegador
- Al finalizar, descarga el reporte CSV

---

## 7️⃣ Solución de Problemas

### Problema: "ChromeDriver no encontrado"

**Solución:**
```bash
pip install --upgrade webdriver-manager
```

Si persiste, instala manualmente siguiendo la [Opción B](#opción-b-instalación-manual-si-la-opción-a-falla)

---

### Problema: "No se puede importar el módulo whatsapp"

**Solución:**
- Verifica que `whatsapp.py` esté en la carpeta `funciones/`
- Asegúrate de que existe `funciones/__init__.py`
- Reinicia Streamlit

---

### Problema: "El código QR no aparece"

**Solución:**
1. Cierra todas las ventanas de Chrome
2. Borra la carpeta `whatsapp_session` en tu proyecto
3. Vuelve a intentar
4. Si persiste, actualiza Chrome a la última versión

---

### Problema: "Números marcados como inválidos pero son correctos"

**Solución:**
- Verifica que el formato sea: `0987654321`
- Elimina espacios en blanco en el Excel
- Asegúrate de que la columna sea de tipo "Texto" no "Número"

---

### Problema: "WhatsApp me bloqueó temporalmente"

**Causas:**
- Enviaste mensajes demasiado rápido
- Enviaste más de 50 mensajes en poco tiempo
- WhatsApp detectó comportamiento automatizado

**Prevención:**
- Usa delays de 10-15 segundos entre mensajes
- No envíes más de 30-40 mensajes por sesión
- Espera unas horas entre tandas de envío
- Varía ligeramente los mensajes

**Solución si fuiste bloqueado:**
- Espera 24 horas
- No intentes enviar más mensajes durante el bloqueo
- Cuando se desbloquee, reduce la cantidad de mensajes

---

### Problema: "El mensaje no se personaliza correctamente"

**Verificación:**
- Las variables deben escribirse exactamente así: `{nombre}` `{apellido}`
- Revisa que las columnas del Excel estén mapeadas correctamente
- Usa la vista previa para verificar

---

## 📞 Soporte Adicional

Si encuentras otros problemas:

1. Verifica que todas las dependencias estén instaladas:
   ```bash
   pip list | grep selenium
   ```

2. Revisa la versión de Python:
   ```bash
   python --version
   ```
   (Debe ser 3.8 o superior)

3. Prueba con un envío pequeño primero (2-3 contactos)

4. Revisa los logs en la terminal donde ejecutas Streamlit

---

## ✅ Checklist Final

Antes de usar en producción, verifica:

- [ ] ChromeDriver instalado y funcionando
- [ ] Dependencias de Python instaladas
- [ ] Archivo `whatsapp.py` en carpeta `funciones/`
- [ ] `app.py` actualizado con nueva opción
- [ ] Excel con formato correcto
- [ ] Teléfonos validados
- [ ] WhatsApp Web funciona en tu navegador
- [ ] Prueba enviada exitosamente (2-3 contactos)

---

## 🎉 ¡Listo!

Tu aplicación ahora está completamente integrada con envío masivo de WhatsApp.

**Recomendaciones finales:**
- Haz pruebas con números de prueba primero
- Usa delays generosos (10-15 segundos)
- No envíes más de 30 mensajes por sesión inicialmente
- Supervisa el primer envío completo
- Guarda siempre los reportes CSV generados

---

**Creado para:** ISTCUMANDA
**Versión:** 1.0
**Fecha:** Febrero 2025
