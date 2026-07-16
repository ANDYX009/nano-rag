import re
from indexador import INDICE_CONOCIMIENTO

# Diccionario de Expansión Semántica (Sinónimos Podológicos)
SINONIMOS_PODOLOGIA = {
    "onicocriptosis": {"unero", "una", "encarnada"},
    "unero": {"onicocriptosis", "una", "encarnada"},
    "micosis": {"hongo", "hongos", "infeccion"},
    "precio": {"costos", "costo", "precio", "cuanto", "pesos"},
    "costo": {"costos", "costo", "precio", "cuanto", "pesos"}
}

def limpiar_texto(texto: str) -> set:
    """Tokeniza el texto, elimina acentos y caracteres especiales."""
    texto_limpio = texto.lower()
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for original, reemplazo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, reemplazo)
    
    palabras = re.findall(r'[a-z0-9]+', texto_limpio)
    tokens = set(palabras)
    
    # EXPANSIÓN SEMÁNTICA: Si la palabra tiene sinónimos, los inyectamos al conjunto
    tokens_expandidos = set(tokens)
    for t in tokens:
        if t in SINONIMOS_PODOLOGIA:
            tokens_expandidos.update(SINONIMOS_PODOLOGIA[t])
            
    return tokens_expandidos

def buscar_fragmento_relevante(pregunta_usuario: str, ruta_archivo: str) -> dict:
    """Escanea el índice en RAM y devuelve la fila con mayor coincidencia de palabras clave."""
    fragmentos = INDICE_CONOCIMIENTO.get(ruta_archivo, [])
    if not fragmentos:
        return {}

    tokens_pregunta = limpiar_texto(pregunta_usuario)
    mejor_fragmento = {}
    max_coincidencias = 0

    for frag in fragmentos:
        tokens_clave = limpiar_texto(frag["palabras_clave"])
        coincidencias = len(tokens_pregunta.intersection(tokens_clave))
        
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
            mejor_fragmento = frag

    return mejor_fragmento
