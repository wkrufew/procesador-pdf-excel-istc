import os
import re
import unicodedata
from pathlib import Path
import pandas as pd

PARTICULAS = ['DE', 'DEL', 'DE LA', 'DE LOS', 'DE LAS', 'SAN', 'SANTA']

def limpiar_cedula(cedula, validar_formato=True):
    if pd.isna(cedula):
        return None
    cedula_str = str(cedula).strip()
    if not validar_formato:
        return cedula_str or None
    cedula_limpia = re.sub(r'[^\d]', '', cedula_str)
    if len(cedula_limpia) != 10 or not cedula_limpia.isdigit():
        return None
    return cedula_limpia

def limpiar_valor_archivo(valor):
    if pd.isna(valor):
        return None
    valor_str = str(valor).strip()
    valor_limpio = re.sub(r'[\\/:*?"<>|]', '', valor_str)
    valor_limpio = re.sub(r'\s+', ' ', valor_limpio).strip()
    return valor_limpio or None

def limpiar_nombres(nombres, validacion_avanzada=True):
    if pd.isna(nombres):
        return None
    nombres_str = str(nombres).strip()
    if not validacion_avanzada:
        nombres_limpio = re.sub(r'\s+', ' ', nombres_str).strip().upper()
        return nombres_limpio or None
    nombres_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ]', ' ', nombres_str)
    nombres_limpio = re.sub(r'\s+', ' ', nombres_limpio).strip()
    nombres_limpio = nombres_limpio.upper()
    palabras = nombres_limpio.split()
    if len(palabras) < 2 or any(len(p) < 2 for p in palabras):
        return None
    return nombres_limpio

def normalizar_texto(texto):
    if not texto:
        return ''
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.upper()
    texto = re.sub(r'[^A-Z\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def normalizar_texto_simple(texto):
    if not texto:
        return ''
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.upper()
    texto = re.sub(r'[^A-Z0-9\s-]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def separar_apellidos_nombres(nombre_completo):
    palabras = nombre_completo.split()
    apellidos, nombres = [], []
    i = 0
    while i < len(palabras) and len(apellidos) < 2:
        if i + 1 < len(palabras) and f"{palabras[i]} {palabras[i+1]}" in PARTICULAS:
            apellidos.append(f"{palabras[i]} {palabras[i+1]}")
            i += 2
        elif palabras[i] in PARTICULAS:
            apellidos.append(palabras[i])
            i += 1
        else:
            apellidos.append(palabras[i])
            i += 1
    if i < len(palabras):
        nombres = palabras[i:]
    return apellidos, nombres

def generar_combinaciones(nombre_completo):
    apellidos, nombres = separar_apellidos_nombres(nombre_completo)
    if not apellidos or not nombres:
        return []
    comb1 = ' '.join(apellidos + nombres)
    comb2 = ' '.join(nombres + apellidos)
    return [normalizar_texto(comb1), normalizar_texto(comb2)]

def generar_combinaciones_simple(valor):
    normalizado = normalizar_texto_simple(valor)
    if not normalizado:
        return []
    return [normalizado]

def procesar_archivos(df, col_cedula, col_nombre, pdf_folder, validar_cedula=True, col_archivo=None, validacion_avanzada=True):
    if col_archivo is None:
        col_archivo = col_cedula

    datos_validos = []
    casos_problematicos = []
    valores_vistos = set()

    for idx, row in df.iterrows():
        cedula_limpia = limpiar_cedula(row[col_cedula], validar_formato=validar_cedula)
        nombres_limpios = limpiar_nombres(row[col_nombre], validacion_avanzada=validacion_avanzada)
        valor_archivo = limpiar_valor_archivo(row[col_archivo])

        motivo = None
        if not cedula_limpia:
            motivo = 'Cédula inválida'
        elif not nombres_limpios:
            motivo = 'Nombre inválido'
        elif not valor_archivo:
            motivo = 'Valor de archivo vacío'
        elif valor_archivo in valores_vistos:
            motivo = 'Valor de archivo duplicado'

        if motivo:
            casos_problematicos.append({'Fila': idx+1, 'Motivo': motivo, 'Cédula': row[col_cedula], 'Nombre': row[col_nombre]})
            continue

        datos_validos.append({'Cédula': cedula_limpia, 'Nombre': nombres_limpios, 'Valor Archivo': valor_archivo})
        valores_vistos.add(valor_archivo)

    df_limpio = pd.DataFrame(datos_validos)

    csv_dict = {}
    for _, row in df_limpio.iterrows():
        if validacion_avanzada:
            combinaciones = generar_combinaciones(row['Nombre'])
        else:
            combinaciones = generar_combinaciones_simple(row['Nombre'])
        csv_dict[row['Valor Archivo']] = {'nombre_original': row['Nombre'], 'combinaciones': combinaciones}

    resultados = []
    for pdf_path in Path(pdf_folder).glob("*.pdf"):
        pdf_name = pdf_path.name
        pdf_name = pdf_name.replace("_", " ")
        pdf_base = re.sub(r'[-_]?SIGNED', '', pdf_name, flags=re.I)
        pdf_base = re.sub(r'\.PDF$', '', pdf_base, flags=re.I)
        pdf_normalizado = normalizar_texto(pdf_base) if validacion_avanzada else normalizar_texto_simple(pdf_base)

        encontrado, valor_match, nombre_csv = False, '', ''
        estado = "Sin coincidencia"

        for valor_archivo, info in csv_dict.items():
            if pdf_normalizado in info['combinaciones']:
                encontrado = True
                valor_match = valor_archivo
                nombre_csv = info['nombre_original']
                nuevo_nombre = f"{valor_archivo}.pdf"
                nuevo_path = pdf_path.parent / nuevo_nombre
                if nuevo_path.exists():
                    estado = "Duplicado ignorado"
                else:
                    os.rename(pdf_path, nuevo_path)
                    estado = "Renombrado"
                break

        resultados.append({
            'PDF original': pdf_name,
            'Nombre CSV': nombre_csv,
            'Valor asignado': valor_match,
            'Estado': estado
        })

    df_resultados = pd.DataFrame(resultados)
    return df_resultados, df_limpio, pd.DataFrame(casos_problematicos)
