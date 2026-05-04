import os
import re
import unicodedata
from pathlib import Path
import pandas as pd

PARTICULAS = ['DE', 'DEL', 'DE LA', 'DE LOS', 'DE LAS', 'SAN', 'SANTA']

def limpiar_cedula(cedula):
    if pd.isna(cedula):
        return None
    cedula_str = str(cedula).strip()
    cedula_limpia = re.sub(r'[^\d]', '', cedula_str)
    if len(cedula_limpia) != 10 or not cedula_limpia.isdigit():
        return None
    return cedula_limpia

def limpiar_nombres(nombres):
    if pd.isna(nombres):
        return None
    nombres_str = str(nombres).strip()
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

def procesar_archivos(df, col_cedula, col_nombre, pdf_folder):
    datos_validos = []
    casos_problematicos = []
    cedulas_vistas = set()

    for idx, row in df.iterrows():
        cedula_limpia = limpiar_cedula(row[col_cedula])
        nombres_limpios = limpiar_nombres(row[col_nombre])

        if not cedula_limpia:
            casos_problematicos.append({'Fila': idx+1, 'Motivo': 'Cédula inválida', 'Cédula': row[col_cedula], 'Nombre': row[col_nombre]})
            continue
        if not nombres_limpios:
            casos_problematicos.append({'Fila': idx+1, 'Motivo': 'Nombre inválido', 'Cédula': row[col_cedula], 'Nombre': row[col_nombre]})
            continue
        if cedula_limpia in cedulas_vistas:
            casos_problematicos.append({'Fila': idx+1, 'Motivo': 'Cédula duplicada', 'Cédula': row[col_cedula], 'Nombre': row[col_nombre]})
            continue

        datos_validos.append({'Cédula': cedula_limpia, 'Nombre': nombres_limpios})
        cedulas_vistas.add(cedula_limpia)

    df_limpio = pd.DataFrame(datos_validos)

    csv_dict = {}
    for _, row in df_limpio.iterrows():
        combinaciones = generar_combinaciones(row['Nombre'])
        csv_dict[row['Cédula']] = {'nombre_original': row['Nombre'], 'combinaciones': combinaciones}

    resultados = []
    for pdf_path in Path(pdf_folder).glob("*.pdf"):
        pdf_name = pdf_path.name
        pdf_name = pdf_name.replace("_", " ")
        pdf_base = re.sub(r'[-_]?SIGNED', '', pdf_name, flags=re.I)
        pdf_base = re.sub(r'\.PDF$', '', pdf_base, flags=re.I)
        pdf_normalizado = normalizar_texto(pdf_base)

        encontrado, cedula_match, nombre_csv = False, '', ''
        estado = "Sin coincidencia"

        for cedula, info in csv_dict.items():
            if pdf_normalizado in info['combinaciones']:
                encontrado = True
                cedula_match = cedula
                nombre_csv = info['nombre_original']
                nuevo_nombre = f"{cedula_match}.pdf"
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
            'Cédula asignada': cedula_match,
            'Estado': estado
        })

    df_resultados = pd.DataFrame(resultados)
    return df_resultados, df_limpio, pd.DataFrame(casos_problematicos)
