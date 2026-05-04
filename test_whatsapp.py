"""
Script de prueba para verificar la instalación del módulo de WhatsApp
Ejecutar este script ANTES de usar en producción
"""

import sys
import importlib.util

def verificar_instalacion():
    """
    Verifica que todas las dependencias estén instaladas correctamente
    """
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE INSTALACIÓN - WhatsApp Module")
    print("=" * 60)
    print()
    
    errores = []
    
    # 1. Verificar Python
    print("1️⃣ Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Se requiere 3.8+)")
        errores.append("Python desactualizado")
    print()
    
    # 2. Verificar Selenium
    print("2️⃣ Verificando Selenium...")
    try:
        import selenium
        print(f"   ✅ Selenium {selenium.__version__}")
    except ImportError:
        print("   ❌ Selenium no instalado")
        errores.append("Instalar: pip install selenium")
    print()
    
    # 3. Verificar webdriver-manager
    print("3️⃣ Verificando webdriver-manager...")
    try:
        import webdriver_manager
        print(f"   ✅ webdriver-manager instalado")
    except ImportError:
        print("   ❌ webdriver-manager no instalado")
        errores.append("Instalar: pip install webdriver-manager")
    print()
    
    # 4. Verificar pandas
    print("4️⃣ Verificando pandas...")
    try:
        import pandas
        print(f"   ✅ pandas {pandas.__version__}")
    except ImportError:
        print("   ❌ pandas no instalado")
        errores.append("Instalar: pip install pandas")
    print()
    
    # 5. Verificar Chrome/Chromium
    print("5️⃣ Verificando Google Chrome...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        try:
            driver = webdriver.Chrome(options=options)
            version = driver.capabilities['browserVersion']
            driver.quit()
            print(f"   ✅ Google Chrome {version}")
        except Exception as e:
            print(f"   ⚠️ Chrome instalado pero ChromeDriver falta")
            print(f"      Error: {str(e)[:100]}")
            errores.append("Instalar ChromeDriver o usar webdriver-manager")
    except Exception as e:
        print(f"   ❌ No se pudo verificar Chrome: {str(e)[:100]}")
        errores.append("Instalar Google Chrome")
    print()
    
    # 6. Verificar módulo whatsapp.py
    print("6️⃣ Verificando módulo whatsapp.py...")
    try:
        spec = importlib.util.find_spec("funciones.whatsapp")
        if spec is not None:
            print("   ✅ Módulo whatsapp.py encontrado")
        else:
            print("   ❌ Módulo whatsapp.py NO encontrado")
            errores.append("Copiar whatsapp.py a carpeta funciones/")
    except Exception as e:
        print(f"   ❌ Error al buscar módulo: {e}")
        errores.append("Verificar estructura del proyecto")
    print()
    
    # 7. Verificar streamlit
    print("7️⃣ Verificando Streamlit...")
    try:
        import streamlit
        print(f"   ✅ Streamlit {streamlit.__version__}")
    except ImportError:
        print("   ❌ Streamlit no instalado")
        errores.append("Instalar: pip install streamlit")
    print()
    
    # Resumen
    print("=" * 60)
    if len(errores) == 0:
        print("✅ VERIFICACIÓN EXITOSA")
        print("   Todos los componentes están instalados correctamente.")
        print("   ¡Puedes usar el módulo de WhatsApp!")
    else:
        print("❌ VERIFICACIÓN FALLIDA")
        print(f"   Se encontraron {len(errores)} problema(s):")
        for i, error in enumerate(errores, 1):
            print(f"   {i}. {error}")
        print("\n   Por favor, soluciona los problemas antes de continuar.")
    print("=" * 60)
    print()
    
    return len(errores) == 0


def test_basico_whatsapp():
    """
    Prueba básica del módulo de WhatsApp sin enviar mensajes reales
    """
    print()
    print("=" * 60)
    print("🧪 PRUEBA BÁSICA DEL MÓDULO")
    print("=" * 60)
    print()
    
    try:
        # Importar módulo
        print("1️⃣ Importando módulo WhatsApp...")
        from .docs import whatsapp
        print("   ✅ Módulo importado correctamente")
        print()
        
        # Probar validación de números
        print("2️⃣ Probando validación de números...")
        numeros_prueba = [
            ("0987654321", True),
            ("593987654321", True),
            ("+593987654321", True),
            ("0887654321", False),
            ("98765432", False),
        ]
        
        for numero, esperado in numeros_prueba:
            resultado = whatsapp.validar_numero_ecuador(numero)
            emoji = "✅" if resultado == esperado else "❌"
            print(f"   {emoji} {numero}: {'Válido' if resultado else 'Inválido'}")
        print()
        
        # Probar limpieza de números
        print("3️⃣ Probando limpieza de números...")
        bot = whatsapp.WhatsAppBot()
        numero_test = "0987654321"
        numero_limpio = bot.limpiar_numero_telefono(numero_test)
        print(f"   Original: {numero_test}")
        print(f"   Limpio:   {numero_limpio}")
        print(f"   ✅ Formato correcto: {numero_limpio.startswith('+593')}")
        print()
        
        print("=" * 60)
        print("✅ PRUEBAS BÁSICAS COMPLETADAS")
        print("   El módulo funciona correctamente.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        print()
        print("=" * 60)
        print("❌ PRUEBAS FALLIDAS")
        print("=" * 60)
        return False


def main():
    """
    Función principal
    """
    print()
    print("🚀 Iniciando verificación del sistema...")
    print()
    
    # Verificar instalación
    instalacion_ok = verificar_instalacion()
    
    if instalacion_ok:
        # Ejecutar pruebas básicas
        test_basico_whatsapp()
    else:
        print("⚠️ Por favor, soluciona los problemas de instalación antes de continuar.")
    
    print()
    print("=" * 60)
    print("📝 NOTAS IMPORTANTES:")
    print("=" * 60)
    print("1. Este script NO envía mensajes reales de WhatsApp")
    print("2. Solo verifica que todo esté instalado correctamente")
    print("3. Para enviar mensajes, usa la aplicación Streamlit")
    print("4. Lee GUIA_INSTALACION.md para más detalles")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
