# 💬 Módulo de Envío Masivo de WhatsApp

## 🎯 Descripción

Este módulo permite enviar mensajes personalizados de WhatsApp a múltiples contactos de forma automatizada usando Selenium y WhatsApp Web.

## ✨ Características

- 📝 Mensajes personalizados con variables
- 📎 Soporte para adjuntar imágenes y PDFs
- ⏱️ Control de velocidad de envío
- ✅ Validación automática de números telefónicos
- 📊 Reporte detallado de envíos
- 🔒 Sesión persistente (no necesitas escanear QR cada vez)

## 🚀 Inicio Rápido

### 1. Preparar tu Excel

Crea un archivo Excel con estas columnas:

```
Nombre    | Apellido  | Teléfono
----------|-----------|-------------
Juan      | Pérez     | 0987654321
María     | González  | 0991234567
```

### 2. Ejecutar la aplicación

```bash
streamlit run app.py
```

### 3. Usar la funcionalidad

1. Selecciona "Envio Masivo de WhatsApp" en el menú
2. Sube tu Excel
3. Configura el mensaje
4. Opcionalmente adjunta un archivo
5. Inicia el envío

## 📝 Variables Disponibles

Puedes usar estas variables en tu mensaje:

- `{nombre}` - Nombre del contacto
- `{apellido}` - Apellido del contacto
- `{nombre_completo}` - Nombre + Apellido

### Ejemplo de mensaje:

```
Hola {nombre} {apellido},

Te saluda el equipo de ISTCUMANDA.

Te recordamos que...

Saludos cordiales.
```

## 📞 Formato de Números

### ✅ Formatos Aceptados

- `0987654321` (Recomendado)
- `593987654321`
- `+593987654321`

### ❌ Formatos No Aceptados

- `98765432` (muy corto)
- `02123456` (teléfono fijo)
- `0887654321` (no es celular)

## ⚙️ Configuración Recomendada

### Delay entre mensajes

| Cantidad de mensajes | Delay recomendado |
|---------------------|-------------------|
| Hasta 10            | 8 segundos        |
| 11-30               | 10-12 segundos    |
| 31-50               | 15 segundos       |

**Importante:** WhatsApp puede bloquearte temporalmente si envías mensajes muy rápido.

## 🔒 Buenas Prácticas

### ✅ Haz esto:

- Prueba con 2-3 contactos primero
- Usa delays de 10+ segundos
- Envía máximo 30-40 mensajes por sesión
- Supervisa el primer envío completo
- Varía los mensajes cuando sea posible

### ❌ Evita esto:

- Enviar más de 50 mensajes seguidos
- Usar delays menores a 5 segundos
- Enviar el mismo mensaje exacto cientos de veces
- Cerrar el navegador durante el envío
- Usar números de teléfono sin validar

## 📊 Reporte de Envíos

Al finalizar, obtendrás un CSV con:

- Número de teléfono
- Nombre y apellido
- Estado del envío (enviado/error)
- Mensaje de error (si aplica)

### Ejemplo de reporte:

| numero         | nombre | apellido | status  | error |
|----------------|--------|----------|---------|-------|
| +593987654321  | Juan   | Pérez    | enviado | None  |
| +593991234567  | María  | González | error   | Número inválido |

## 🛠️ Solución de Problemas Comunes

### El QR no aparece

**Solución:**
1. Cierra Chrome completamente
2. Borra la carpeta `whatsapp_session`
3. Vuelve a intentar

### Mensajes no se envían

**Verificar:**
- ¿Escaneaste el QR?
- ¿Los números son válidos?
- ¿Hay conexión a Internet?
- ¿Chrome está actualizado?

### WhatsApp me bloqueó

**Causas comunes:**
- Envío muy rápido
- Muchos mensajes en poco tiempo
- Comportamiento automatizado detectado

**Solución:**
- Espera 24 horas
- Reduce velocidad de envío
- Usa delays más largos

### Números marcados como inválidos

**Solución:**
- Verifica el formato en Excel
- Elimina espacios y guiones
- Asegúrate que sean celulares (09...)

## 🔐 Seguridad y Privacidad

### Datos de sesión

- La sesión de WhatsApp se guarda en: `whatsapp_session/`
- Esta carpeta contiene tus credenciales encriptadas
- **NO compartas esta carpeta**
- **NO la subas a repositorios públicos**

### Agregar al .gitignore:

```gitignore
# WhatsApp session data
whatsapp_session/
temp_adjuntos/
*.session
```

## 📈 Límites y Restricciones

### Límites técnicos:

- ⚠️ WhatsApp puede limitar cuentas con uso excesivo
- ⚠️ No hay límite técnico en el código, pero recomendamos máximo 50 mensajes/hora
- ⚠️ Los archivos adjuntos deben ser menores a 16MB (límite de WhatsApp)

### Limitaciones del método:

- Requiere que WhatsApp Web esté activo
- Necesita supervisión (aunque sea mínima)
- Más lento que la API oficial pero gratuito
- Puede ser detectado como automatización

## 🆚 Comparación con API Oficial

| Característica          | Este módulo (Selenium) | API Oficial WhatsApp |
|------------------------|------------------------|----------------------|
| **Costo**              | ✅ Gratis              | 💰 Pago              |
| **Configuración**      | ✅ Simple              | ⚠️ Compleja          |
| **Límites**            | ⚠️ ~50 msg/hora       | ✅ Miles/hora        |
| **Estabilidad**        | ⚠️ Media              | ✅ Alta              |
| **Mejor para**         | Uso esporádico         | Uso empresarial      |

## 🎓 Casos de Uso Ideales

✅ **Perfecto para:**
- Envío de recordatorios a estudiantes (20-30 personas)
- Notificaciones de eventos
- Confirmaciones de inscripción
- Comunicados ocasionales

❌ **No recomendado para:**
- Campañas masivas diarias
- Marketing agresivo
- Más de 100 mensajes al día
- Servicios 24/7 automatizados

## 💡 Tips Avanzados

### Personalización avanzada

Puedes combinar variables en el mensaje:

```
Estimado/a {nombre_completo},

Gracias por inscribirte en {curso}.
Tu código de estudiante es: {codigo}
```

### Múltiples tandas

Para enviar a más de 50 personas:

1. Divide el Excel en grupos de 30
2. Envía el primer grupo
3. Espera 2-3 horas
4. Envía el siguiente grupo

### Programar envíos

Puedes usar PyWhatKit para programar:

```python
import pywhatkit

# Enviar a las 14:30
pywhatkit.sendwhatmsg("+593987654321", "Hola", 14, 30)
```

## 🔄 Actualizaciones Futuras

Posibles mejoras planificadas:

- [ ] Soporte para grupos de WhatsApp
- [ ] Programación de envíos
- [ ] Plantillas de mensajes guardadas
- [ ] Estadísticas de lectura
- [ ] Integración con base de datos

## 📚 Recursos Adicionales

- [Documentación de Selenium](https://selenium-python.readthedocs.io/)
- [WhatsApp Business API](https://business.whatsapp.com/)
- [Políticas de WhatsApp](https://www.whatsapp.com/legal/business-policy)

## ⚖️ Consideraciones Legales

**Importante:**
- Asegúrate de tener consentimiento para contactar a las personas
- Respeta las políticas de WhatsApp sobre spam
- No uses para marketing no solicitado
- Cumple con leyes de protección de datos de tu país

## 🤝 Contribuciones

Si encuentras bugs o tienes sugerencias:

1. Documenta el problema claramente
2. Incluye pasos para reproducirlo
3. Comparte versiones de software usadas

## 📄 Licencia

Este módulo es parte del proyecto ISTCUMANDA.

---

**Versión:** 1.0  
**Última actualización:** Febrero 2025  
**Mantenido por:** Equipo ISTCUMANDA
