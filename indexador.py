import csv
import os

# El estado global en RAM que actuará como base de datos dinámica
INDICE_CONOCIMIENTO = {}

def cargar_csv_en_ram(ruta_archivo: str) -> None:
    """Lee el CSV y actualiza de golpe el índice global en RAM de forma limpia."""
    global INDICE_CONOCIMIENTO
    
    if not os.path.exists(ruta_archivo):
        print(f"[ERROR] No se pudo indexar. Archivo no encontrado: {ruta_archivo}")
        return

    nuevos_fragmentos = []
    
    with open(ruta_archivo, mode="r", encoding="utf-8") as f:
        # DictReader lee la primera fila automáticamente como los nombres de las columnas
        lector = csv.DictReader(f)
        
        for fila in lector:
            # Limpiamos y extraemos las columnas definidas en el contrato técnico
            nuevos_fragmentos.append({
                "categoria": fila.get("categoria", "").strip(),
                "palabras_clave": fila.get("palabras_clave", "").lower().strip(),
                "respuesta_oficial": fila.get("respuesta_oficial", "").strip()
            })
            
    # Reemplazo atómico en memoria RAM para evitar corrupción de datos
    INDICE_CONOCIMIENTO[ruta_archivo] = nuevos_fragmentos
    print(f"[INDEX] {len(nuevos_fragmentos)} filas cargadas con éxito en RAM desde {ruta_archivo}.")
