import requests
import sqlite3
import time
from bs4 import BeautifulSoup
import re
#Intamos la conexión con la libreria requests, considerando que si algo falla se vea el error.
while True:
    try:
        response = requests.get("https://es.wikipedia.org/wiki/Anexo:Sencillos_n%C3%BAmero_uno_en_Espa%C3%B1a#Canciones_con_m%C3%A1s_semanas_en_el_n%C3%BAmero_uno")
        time.sleep(5)
        break
    except Exception as e:
        print("Ha ocurrido un error al conectarse", e)

soup = BeautifulSoup(response.text, "html.parser")


#Busca la tabla y acceder al contenido.
tabla = soup.find('table', {'class': 'wikitable'})
cuerpo = tabla.find('tbody')

# Extraer todas las filas, ignorando la primera linea, que simplemente son los encabezados.
filas = cuerpo.find_all('tr')[1:]



datos = []
ultimo_puesto = None
ultimo_semanas = None

for fila in filas:
    celdas = fila.find_all('td')
    texto_celdas = [celda.get_text(strip=True) for celda in celdas]
    
    # Rellenar con valores anteriores si faltan datos
    if len(texto_celdas) == 6:
        # Fila completa: tomar todos los datos
        ultimo_puesto = texto_celdas[0]
        titulo, interprete, año, semanas, pais = texto_celdas[1:]
        ultimo_semanas = semanas
    elif len(texto_celdas) == 5: 
        titulo, interprete, año, semanas, pais = texto_celdas
        ultimo_puesto = ultimo_puesto  # Se conserva
        ultimo_semanas = semanas
    elif len(texto_celdas) == 4:
        titulo, interprete, año, pais = texto_celdas
        semanas = ultimo_semanas
    else:
        texto_celdas.extend(["Desconocido"] * (5 - len(texto_celdas)))
        titulo, interprete, año, semanas, pais = texto_celdas
    mitad = len(pais) // 2
    if len(pais) % 2 == 0 and pais[:mitad] == pais[mitad:]:
        pais[:mitad]
    
    # Caso 2: duplicación de palabras o frases (ColombiaColombiaTrinidad y TobagoTrinidad y Tobago)
    
    # Intenta dividir el texto por mayúsculas (cuando no hay espacios)
    partes = re.findall(r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ]?[a-záéíóúñ]+)*', pais)
    
    resultado = []
    i = 0
    while i < len(partes):
        if i + 1 < len(partes) and partes[i] == partes[i + 1]:
            resultado.append(partes[i])
            i += 2
        else:
            resultado.append(partes[i])
            i += 1
    pais = " ".join(resultado)
    

    datos.append((titulo, interprete, año[:4], semanas, pais))

#crear conexión y base de datos
conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS canciones_con_mas_semanas_en_el_numero_uno")
cursor.execute("CREATE TABLE IF NOT EXISTS canciones_con_mas_semanas_en_el_numero_uno(titulo text,interprete text, año int,semanas int,pais text)")
cursor.executemany("INSERT INTO canciones_con_mas_semanas_en_el_numero_uno values (?,?,?,?,?)", datos)
conn.commit()
conn.close()

print("Primeras canciones insertadas:")
for fila in datos[:5]:
    print(fila)