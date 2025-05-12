import requests
import sqlite3
import time
from bs4 import BeautifulSoup
import re

URL = "https://es.wikipedia.org/wiki/Anexo:Sencillos_n%C3%BAmero_uno_en_Espa%C3%B1a#Canciones_con_m%C3%A1s_semanas_en_el_n%C3%BAmero_uno"
BD_TOP_CANCIONES = "Top_Canciones_Numero_uno_en_españa.db"
# Iniciamos la conexión con la libreria requests, considerando que si algo falla se vea el error.
while True:
    try:
        response = requests.get(URL)
        time.sleep(2) #esperamos dos segundos para no saturar la pagina
        break
    except Exception as e:
        print("Ha ocurrido un error al conectarse", e)

soup = BeautifulSoup(response.text, "html.parser") 


# Busca la tabla y accede al contenido.
tabla = soup.find("table", {"class": "wikitable"})
cuerpo = tabla.find("tbody")

# Extraer todas las filas, ignorando la primera linea, que simplemente son los encabezados.
filas = cuerpo.find_all("tr")[1:] 

"""
Dado que en algunos puestos, varias canciones estan compartiendo el lugar en la tabla, al hacer scrapping; Obteniamos menos información.
Las semanas por ejemplo.

"""
datos = []
ultimo_semanas = None

for fila in filas:
    celdas = fila.find_all("td")
    texto_celdas = [celda.get_text(strip=True) for celda in celdas]

    # Rellenar con valores anteriores si faltan datos
    if len(texto_celdas) == 6:
        # Fila completa: tomar todos los datos, exceptuando el puesto que no lo necesitamos ya que genera conflictos. 
        titulo, interprete, año, semanas, pais = texto_celdas[1:] 
        ultimo_semanas = semanas #guardamos el valor de semanas, por si en la siguiente fila, es el dato que falta
    elif len(texto_celdas) == 5: 
        titulo, interprete, año, semanas, pais = texto_celdas #este es nuestro caso ideal donde solo falta el puesto
        ultimo_semanas = semanas #lo mismo que en el caso anterior
    elif len(texto_celdas) == 4: #aqui falta el puesto y las semanas, semanas que usaremos de la ultima fila que nos haya aportado el dato
        titulo, interprete, año, pais = texto_celdas
        semanas = ultimo_semanas
    else:
        texto_celdas.extend(["Desconocido"] * (5 - len(texto_celdas))) #si se diera un caso donde tiene menos de 4 datos la fila. se rellenaria con "desconocido"
        titulo, interprete, año, semanas, pais = texto_celdas
    mitad = len(pais) // 2 
    if len(pais) % 2 == 0 and pais[:mitad] == pais[mitad:]: #En el campo del pais la informacion se repetia, entonces estoy diviendo el campo a la mitad. si es exactamente simetrico
        pais =pais[:mitad]
    #Intenta dividir el texto por mayúsculas (cuando no hay espacios). para los casos donde hay mas de un pais repetido y no es exactamente simetrico para dividir
    partes = re.findall(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ]?[a-záéíóúñ]+)*", pais)

    resultado = []
    i = 0
    while i < len(partes): #analiza las partes cortadas, 
        if i + 1 < len(partes) and partes[i] == partes[i + 1]:
            resultado.append(partes[i])
            i += 2
        else:
            resultado.append(partes[i])
            i += 1
    pais = " ".join(resultado) #luego lo junta sin la repetición
    interprete = interprete.split("con")[0] # como en wikipedia el conector entre los nombres de los artistas era "con". decidi que se cortara ahi. para solo usar el primer artista
    datos.append((titulo, interprete, año[:4], semanas, pais))  #al final del proceso se guardan los datos de la fila en la lista datos

# crear conexión y base de datos
conn = sqlite3.connect(BD_TOP_CANCIONES)
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS canciones_con_mas_semanas_en_el_numero_uno") #eliminamos la tabla si ya existe
cursor.execute(
    "CREATE TABLE IF NOT EXISTS canciones_con_mas_semanas_en_el_numero_uno(titulo text,interprete text, año int,semanas int,pais text)"
) #Comprobamos efectivamente que no exista la tabla para crearla sin errores
cursor.executemany(
    "INSERT INTO canciones_con_mas_semanas_en_el_numero_uno values (?,?,?,?,?)", datos 
) #se insertan las filas
conn.execute(
    "ALTER TABLE canciones_con_mas_semanas_en_el_numero_uno ADD COLUMN idioma TEXT"
) #se crea la columna idioma
conn.execute(
    "ALTER TABLE canciones_con_mas_semanas_en_el_numero_uno ADD COLUMN continente TEXT"
) #se crea la columna continente
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
    """ #Le asignamos un continente segun el pais, use like por si algun pais secundario se hubiese quedado en la base de datos. asi se tiene en cuenta el primer pais que encuentre
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
    """) #Asigna el idioma de cada cancion manualmente buscada. como en español eran la mayoria. SOLO expecifique los casos que son en otras lenguas.
conn.commit()
conn.close()

#Canción más antigua de la lista

def Cancion_mas_antigua():
    conn = sqlite3.connect(BD_TOP_CANCIONES)
    conn.row_factory = sqlite3.Row  # Acceso a columnas por nombre, hace más claro el extraer información. como si se tratase de un diccionario.
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canciones_con_mas_semanas_en_el_numero_uno ORDER BY año ASC LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()

    print(f"""La canción más antigua en este top es: "{resultado['titulo']}", con {resultado['semanas']} semanas en el top.
Autor: {resultado['interprete']}, que es de {resultado['pais']}, {resultado['continente']}
Año: {resultado['año']}
Idioma principal: {resultado['idioma']}
""")
    
#¿Qué artista aparece más veces en esta lista?
def Artista_con_mas_apariciones():
    conn = sqlite3.connect(BD_TOP_CANCIONES)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("""
    SELECT interprete, count(*) AS apariciones
    FROM canciones_con_mas_semanas_en_el_numero_uno
    GROUP BY interprete 
    ORDER BY apariciones DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"El artista que más aparece en esta lista es {resultado['interprete']}, {resultado['apariciones']} veces.")

#¿Qué país tiene más artistas en esta lista?

def Pais_con_mas_apariciones():
    conn = sqlite3.connect(BD_TOP_CANCIONES)
    conn.row_factory = sqlite3.Row  
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
    conn = sqlite3.connect(BD_TOP_CANCIONES)
    conn.row_factory = sqlite3.Row 
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
    conn = sqlite3.connect(BD_TOP_CANCIONES)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("""
    SELECT continente, count(*) AS continente_apariciones
    FROM canciones_con_mas_semanas_en_el_numero_uno
    GROUP BY continente
    ORDER BY continente_apariciones DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"El continente que más aparece en esta lista es {resultado['continente']}, {resultado['continente_apariciones']} veces.")

#¿Qué canción ha estado más % de tiempo al año como número 1?
def Cancion_con_porcentaje_de_apariciones():
    conn = sqlite3.connect(BD_TOP_CANCIONES)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("""
    SELECT titulo, (semanas/0.52) AS porcentaje_anual
    FROM canciones_con_mas_semanas_en_el_numero_uno 
    WHERE semanas > 0
    ORDER BY porcentaje_anual DESC LIMIT 1""")
    resultado = cursor.fetchone()
    conn.close()
    print(f"""La canción que tiene más porcentaje de tiempo anual, en el número uno, es "{resultado['titulo']}", con {resultado['porcentaje_anual']:.2f} % .""")

def menu(): #Un menú basico y simple. con un diccionario que permite acceder a las funciones
    opciones = {
        1: Cancion_mas_antigua,
        2: Artista_con_mas_apariciones,
        3: Pais_con_mas_apariciones,
        4: Canciones_por_idioma,
        5: Continente_con_mas_apariciones,
        6: Cancion_con_porcentaje_de_apariciones,
        0: exit #sale del programa
    }

    while True: #bucle infinito
        print("\n--- MENÚ DE CONSULTAS ---")
        print("1. Mostrar la canción más antigua del top")
        print("2. Mostrar el artista con más apariciones en el top")
        print("3. Mostrar el país con más artistas en la lista")
        print("4. Mostrar cuántas canciones hay por idioma")
        print("5. Mostrar el continente con más apariciones")
        print("6. Mostrar la canción con mayor % de tiempo como número 1")
        print("0. Salir")

        try: #comprueba que el usuario ingrese un número
            opcion = int(input("Selecciona una opción: "))
            if opcion in opciones: #Sí el número esta en el diccionario, llama a la función
                opciones[opcion]()  
            else:
                print("Opción no válida, intenta de nuevo.") #Si el número no está en el diccionario. Vuelve al menú
        except ValueError: #en caso de error(input invalido por ejemplo)
            print("Por favor ingresa un número.")

print("\n----- CANCIONES CON MÁS SEMANAS EN EL TOP 1 DE ESPAÑA -----") #Titulo principal que ve el usuario al iniciar el programa
menu() #Inicializamos el menú