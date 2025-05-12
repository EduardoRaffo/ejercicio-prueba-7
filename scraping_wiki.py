import requests
import sqlite3
import time
from bs4 import BeautifulSoup
import re

# Intamos la conexión con la libreria requests, considerando que si algo falla se vea el error.
while True:
    try:
        response = requests.get(
            "https://es.wikipedia.org/wiki/Anexo:Sencillos_n%C3%BAmero_uno_en_Espa%C3%B1a#Canciones_con_m%C3%A1s_semanas_en_el_n%C3%BAmero_uno"
        )
        time.sleep(2)
        break
    except Exception as e:
        print("Ha ocurrido un error al conectarse", e)

soup = BeautifulSoup(response.text, "html.parser")


# Busca la tabla y acceder al contenido.
tabla = soup.find("table", {"class": "wikitable"})
cuerpo = tabla.find("tbody")

# Extraer todas las filas, ignorando la primera linea, que simplemente son los encabezados.
filas = cuerpo.find_all("tr")[1:]


datos = []
ultimo_puesto = None
ultimo_semanas = None

for fila in filas:
    celdas = fila.find_all("td")
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
    partes = re.findall(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ]?[a-záéíóúñ]+)*", pais)

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
    interprete = interprete.split("con")[0]
    datos.append((titulo, interprete, año[:4], semanas, pais))

# crear conexión y base de datos
conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS canciones_con_mas_semanas_en_el_numero_uno")
cursor.execute(
    "CREATE TABLE IF NOT EXISTS canciones_con_mas_semanas_en_el_numero_uno(titulo text,interprete text, año int,semanas int,pais text)"
)
cursor.executemany(
    "INSERT INTO canciones_con_mas_semanas_en_el_numero_uno values (?,?,?,?,?)", datos
)
conn.execute(
    "ALTER TABLE canciones_con_mas_semanas_en_el_numero_uno ADD COLUMN idioma TEXT"
)
conn.execute(
    "ALTER TABLE canciones_con_mas_semanas_en_el_numero_uno ADD COLUMN continente TEXT"
)
conn.commit()
conn.execute(
    """
    UPDATE canciones_con_mas_semanas_en_el_numero_uno
    SET continente = CASE
        WHEN pais LIKE 'España%' THEN 'Europa'
        WHEN pais LIKE 'Suecia%' THEN 'Europa'
        WHEN pais LIKE 'Estados Unidos%' THEN 'América del Norte'
        WHEN pais LIKE 'Francia%' THEN 'Europa'
        WHEN pais LIKE 'Reino Unido%' THEN 'Europa'
        WHEN pais LIKE 'Argentina%' THEN 'América del Sur'
        WHEN pais LIKE 'Colombia%' THEN 'América del Sur'
        WHEN pais LIKE 'Cuba%' THEN 'América del Norte'
        WHEN pais LIKE 'Alemania%' THEN 'Europa'
        WHEN pais LIKE 'Brasil%' THEN 'América del Sur'
        WHEN pais LIKE 'Venezuela%' THEN 'América del Sur'
        WHEN pais LIKE 'Guyana%' THEN 'América del Sur'
        WHEN pais LIKE 'Puerto Rico%' THEN 'América del Norte'
        WHEN pais LIKE 'Canadá%' THEN 'América del Norte'
        ELSE 'Desconocido'
    END;
    """
)
conn.execute(
    """
    UPDATE canciones_con_mas_semanas_en_el_numero_uno
    SET idioma = CASE
        WHEN titulo LIKE 'Lambada%' THEN 'Portugués'
        WHEN titulo LIKE 'Ai Se Eu%' THEN 'Portugués'
        WHEN titulo LIKE 'Voyage%' THEN 'Francés'
        WHEN titulo LIKE 'Waka%' THEN 'Inglés'
        WHEN titulo LIKE 'You''re%' THEN 'Inglés'
        WHEN titulo LIKE 'Gimme%' THEN 'Inglés'
        WHEN titulo LIKE 'On%' THEN 'Inglés'
        WHEN titulo LIKE 'Candle%' THEN 'Inglés'
        WHEN titulo LIKE 'Mambo%' THEN 'Inglés'
        WHEN titulo LIKE 'Always%' THEN 'Inglés'
        WHEN titulo LIKE 'Infinity%' THEN 'Inglés'
        WHEN titulo LIKE 'The Final%' THEN 'Inglés'
        WHEN titulo LIKE 'Sorry%' THEN 'Inglés'
        ELSE 'Español'
    END;
    """)
conn.commit()
conn.close()

#Canción más antigua de la lista

def Cancion_mas_antigua():
    conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canciones_con_mas_semanas_en_el_numero_uno ORDER BY año ASC LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()

    print(f"""La canción más antigua en este top es: {resultado['titulo']}, con {resultado['semanas']} semanas en el top.
Autor: {resultado['interprete']}, que es de {resultado['pais']}, {resultado['continente']}
Año: {resultado['año']}
Idioma principal: {resultado['idioma']}
""")
    
#¿Qué artista aparece más veces en esta lista?
def Artista_con_mas_apariciones():
    conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre
    cursor = conn.cursor()
    cursor.execute("""
    SELECT interprete, count(*) AS apariciones
    FROM canciones_con_mas_semanas_en_el_numero_uno
    GROUP BY interprete 
    ORDER BY apariciones DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"El artista que más aparece en esta lista es {resultado['interprete']}, con {resultado['apariciones']} veces.")

#¿Qué país tiene más artistas en esta lista?

def Pais_con_mas_apariciones():
    conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre
    cursor = conn.cursor()
    cursor.execute("""
    SELECT pais, COUNT(DISTINCT interprete) AS total_artistas_pais
    FROM canciones_con_mas_semanas_en_el_numero_uno
    GROUP BY pais 
    ORDER BY total_artistas_pais DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"El país que más aparece en esta lista es {resultado['pais']}, con {resultado['total_artistas_pais']} artistas.")

#¿Cuantas canciones distintas hay por cada idioma?
def Canciones_por_idioma():
    conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre
    cursor = conn.cursor()
    cursor.execute("""
    SELECT idioma, COUNT(DISTINCT titulo) AS total_canciones_idioma
    FROM canciones_con_mas_semanas_en_el_numero_uno
    GROUP BY idioma 
    ORDER BY total_canciones_idioma DESC""")
    resultado = cursor.fetchall()
    conn.close()
    for linea in resultado:
        print(f"{linea['idioma']}, con {linea['total_canciones_idioma']} canciones.")

#¿Cuál es el continente con más apariciones en la lista?
def Continente_con_mas_apariciones():
    conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre
    cursor = conn.cursor()
    cursor.execute("""
    SELECT continente, count(*) AS continente_apariciones
    FROM canciones_con_mas_semanas_en_el_numero_uno
    GROUP BY continente
    ORDER BY continente_apariciones DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"El continente que más aparece en esta lista es {resultado['continente']}, con {resultado['continente_apariciones']} veces.")

#¿Qué canción ha estado más % de tiempo al año como número 1?
def Cancion_con_porcentaje_de_apariciones():
    conn = sqlite3.connect("Top_Canciones_Numero_uno_en_españa.db")
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre
    cursor = conn.cursor()
    cursor.execute("""
    SELECT titulo, (semanas/0.52) AS porcentaje_anual
    FROM canciones_con_mas_semanas_en_el_numero_uno 
    WHERE semanas > 0
    ORDER BY porcentaje_anual DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"La canción que tiene más porcentaje de tiempo anual, en el número uno, es {resultado['titulo']}, con {resultado['porcentaje_anual']:.2f} % .")
