import pandas as pd
import re
import smtplib
import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EMAIL_EMISOR = os.getenv("SMTP_EMAIL", "soporte@istcumanda.edu.ec")
PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "mail.istcumanda.edu.ec")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

def correo_valido(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, str(correo).strip())

def enviar_correos(df, col_correo, col_nombre=None, col_cargo=None,
                   html_template=None, logo_file=None, pie_correo=None,
                   asunto="Mensaje ISTCUMANDA"):
    resultados = []

    logo_encoded = None
    if logo_file:
        logo_bytes = logo_file.read()
        logo_encoded = base64.b64encode(logo_bytes).decode()

    for _, row in df.iterrows():
        destinatario = str(row.get(col_correo)).strip()
        nombre = str(row.get(col_nombre, "")) if col_nombre else ""
        cargo = str(row.get(col_cargo, "")) if col_cargo else ""
        usuario = str(row.get("usuario", ""))
        contrasena = str(row.get("contrasena", ""))

        if not destinatario or not correo_valido(destinatario):
            resultados.append({"correo": destinatario, "nombre": nombre, "cargo": cargo,
                               "estado": "Fallo", "detalle": "Correo inválido o vacío",
                               "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            continue

        html = html_template or ""
        html = html.replace("{nombre}", nombre)\
                   .replace("{cargo}", cargo)\
                   .replace("{usuario}", usuario)\
                   .replace("{contrasena}", contrasena)

        if logo_encoded:
            html = f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_encoded}" width="150"></div>' + html

        mensaje = MIMEMultipart("related")
        mensaje["From"] = EMAIL_EMISOR
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_EMISOR, PASSWORD)
                server.sendmail(EMAIL_EMISOR, destinatario, mensaje.as_string())
            resultados.append({"correo": destinatario, "nombre": nombre, "cargo": cargo,
                               "estado": "Enviado", "detalle": "",
                               "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        except Exception as e:
            resultados.append({"correo": destinatario, "nombre": nombre, "cargo": cargo,
                               "estado": "Fallo", "detalle": str(e),
                               "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    return pd.DataFrame(resultados)
