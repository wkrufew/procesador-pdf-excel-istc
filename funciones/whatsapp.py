"""
Módulo de envío masivo de WhatsApp usando Selenium
Permite enviar mensajes personalizados con archivos adjuntos opcionales
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pathlib import Path
from webdriver_manager.chrome import ChromeDriverManager
import re


class WhatsAppBot:
    """
    Bot para envío masivo de mensajes de WhatsApp
    """
    
    def __init__(self, delay_entre_mensajes=10):
        """
        Inicializa el bot de WhatsApp
        
        Args:
            delay_entre_mensajes (int): Segundos de espera entre cada mensaje
        """
        self.delay = delay_entre_mensajes
        self.driver = None
        
    def iniciar_navegador(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Mantener sesión
        chrome_options.add_argument("--profile-directory=Default")

        service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.get("https://web.whatsapp.com")
        return True
    
    def esperar_login(self, timeout=60):
        """
        Espera a que el usuario escanee el código QR
        
        Args:
            timeout (int): Tiempo máximo de espera en segundos
            
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            # Esperar a que aparezca la barra de búsqueda (señal de login exitoso)
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            return True
        except TimeoutException:
            return False
    
    def limpiar_numero_telefono(self, numero):
        """
        Limpia y formatea el número de teléfono
        
        Args:
            numero (str): Número de teléfono
            
        Returns:
            str: Número limpio en formato internacional
        """
        # Eliminar espacios, guiones y paréntesis
        numero = str(numero).strip()
        numero = re.sub(r'[\s\-\(\)]', '', numero)
        
        # Si empieza con 0, reemplazar por código de Ecuador +593
        if numero.startswith('0'):
            numero = '593' + numero[1:]
        
        # Si no tiene código de país, agregar +593
        if not numero.startswith('+') and not numero.startswith('593'):
            numero = '593' + numero
        
        # Asegurar que tenga el +
        if not numero.startswith('+'):
            numero = '+' + numero
            
        return numero
    
    def enviar_mensaje(self, numero, mensaje, archivo_adjunto=None):
        """
        Envía un mensaje a un número de WhatsApp
        
        Args:
            numero (str): Número de teléfono en formato internacional
            mensaje (str): Texto del mensaje
            archivo_adjunto (str): Ruta al archivo adjunto (opcional)
            
        Returns:
            dict: Resultado del envío con status y detalles
        """
        resultado = {
            'numero': numero,
            'status': 'pendiente',
            'error': None
        }
        
        try:
            # Limpiar número
            numero_limpio = self.limpiar_numero_telefono(numero)
            
            # Abrir chat usando URL directa
            url = f"https://web.whatsapp.com/send?phone={numero_limpio}"
            self.driver.get(url)
            
            # Esperar a que cargue el chat
            time.sleep(3)
            
            # Buscar el cuadro de texto
            input_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            
            # Si hay archivo adjunto, enviarlo primero
            if archivo_adjunto and Path(archivo_adjunto).exists():
                resultado_adjunto = self._enviar_archivo(archivo_adjunto)
                if not resultado_adjunto:
                    resultado['status'] = 'error'
                    resultado['error'] = 'Error al enviar archivo adjunto'
                    return resultado
                time.sleep(2)
            
            # Enviar mensaje de texto
            # Dividir mensaje por saltos de línea y enviar
            lineas = mensaje.split('\n')
            for i, linea in enumerate(lineas):
                input_box.send_keys(linea)
                if i < len(lineas) - 1:  # No enviar SHIFT+ENTER en la última línea
                    input_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            # Enviar mensaje
            input_box.send_keys(Keys.ENTER)
            
            # Esperar a que se envíe
            time.sleep(2)
            
            resultado['status'] = 'enviado'
            return resultado
            
        except TimeoutException:
            resultado['status'] = 'error'
            resultado['error'] = 'Número inválido o no existe en WhatsApp'
            return resultado
        except Exception as e:
            resultado['status'] = 'error'
            resultado['error'] = str(e)
            return resultado
    
    def _enviar_archivo(self, ruta_archivo):
        """
        Envía un archivo adjunto (imagen o PDF)
        
        Args:
            ruta_archivo (str): Ruta al archivo
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Buscar botón de adjuntar
            attach_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@title="Adjuntar"]'))
            )
            attach_btn.click()
            time.sleep(1)
            
            # Buscar input de archivo (está oculto)
            file_input = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            
            if file_input:
                # Convertir ruta a absoluta
                ruta_absoluta = str(Path(ruta_archivo).resolve())
                file_input[0].send_keys(ruta_absoluta)
                time.sleep(2)
                
                # Buscar y hacer clic en botón de enviar
                send_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                )
                send_btn.click()
                time.sleep(3)
                
                return True
            return False
            
        except Exception as e:
            print(f"Error al enviar archivo: {e}")
            return False
    
    def enviar_mensajes_masivos(self, df, col_numero, col_nombre, col_apellido, 
                                 mensaje_template, archivo_adjunto=None, 
                                 callback_progreso=None):
        """
        Envía mensajes masivos a una lista de contactos
        
        Args:
            df (DataFrame): DataFrame con los datos
            col_numero (str): Nombre de columna con números
            col_nombre (str): Nombre de columna con nombres
            col_apellido (str): Nombre de columna con apellidos
            mensaje_template (str): Template del mensaje con variables {nombre}, {apellido}
            archivo_adjunto (str): Ruta al archivo adjunto (opcional)
            callback_progreso (function): Función callback para reportar progreso
            
        Returns:
            DataFrame: Resultados del envío
        """
        resultados = []
        total = len(df)

        for counter, (_, row) in enumerate(df.iterrows(), start=1):
            # Preparar datos
            numero = row[col_numero]
            nombre = row.get(col_nombre, '') if col_nombre else ''
            apellido = row.get(col_apellido, '') if col_apellido else ''

            # Personalizar mensaje
            mensaje = mensaje_template.replace('{nombre}', str(nombre))
            mensaje = mensaje.replace('{apellido}', str(apellido))
            mensaje = mensaje.replace('{nombre_completo}', f"{nombre} {apellido}".strip())

            # Enviar mensaje
            resultado = self.enviar_mensaje(numero, mensaje, archivo_adjunto)
            resultado['nombre'] = nombre
            resultado['apellido'] = apellido
            resultados.append(resultado)

            # Callback de progreso
            if callback_progreso:
                callback_progreso(counter, total, resultado)

            # Delay entre mensajes (excepto el último)
            if counter < total:
                time.sleep(self.delay)
        
        # Convertir a DataFrame
        df_resultados = pd.DataFrame(resultados)
        return df_resultados
    
    def cerrar(self):
        """
        Cierra el navegador
        """
        if self.driver:
            self.driver.quit()


def validar_numero_ecuador(numero):
    """
    Valida si un número de teléfono ecuatoriano es válido
    
    Args:
        numero (str): Número de teléfono
        
    Returns:
        bool: True si es válido
    """
    numero = str(numero).strip()
    numero = re.sub(r'[\s\-\(\)]', '', numero)
    
    # Validar formato ecuatoriano (09xxxxxxxx o 593xxxxxxxxx)
    if re.match(r'^0[9][0-9]{8}$', numero):
        return True
    if re.match(r'^593[9][0-9]{8}$', numero):
        return True
    if re.match(r'^\+593[9][0-9]{8}$', numero):
        return True
    
    return False


def procesar_excel_whatsapp(df, col_numero):
    """
    Procesa el Excel y valida números de teléfono
    
    Args:
        df (DataFrame): DataFrame con datos
        col_numero (str): Nombre de columna con números
        
    Returns:
        tuple: (df_validos, df_invalidos)
    """
    df = df.copy()
    df['numero_valido'] = df[col_numero].apply(validar_numero_ecuador)
    
    df_validos = df[df['numero_valido']].copy()
    df_invalidos = df[~df['numero_valido']].copy()
    
    return df_validos, df_invalidos
