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
            # Determinamos dinámicamente el esquema del archivo CSV
            categoria = fila.get("categoria", "").strip()
            
            if "concepto" in fila:
                # Esquema para clinica_info.csv (Horarios y Precios)
                concepto = fila.get("concepto", "").strip()
                detalle = fila.get("detalle", "").strip()
                
                # Combinamos categoría y concepto para darle contexto léxico al buscador
                palabras_clave = f"{categoria} {concepto}".lower().strip()
                respuesta_oficial = detalle
            else:
                # Esquema original para podologia_faq.csv
                palabras_clave = fila.get("palabras_clave", "").lower().strip()
                respuesta_oficial = fila.get("respuesta_oficial", "").strip()
            
            # Limpiamos y extraemos las columnas normalizadas según el contrato técnico
            nuevos_fragmentos.append({
                "categoria": categoria,
                "palabras_clave": palabras_clave,
                "respuesta_oficial": respuesta_oficial
            })
            
    # Reemplazo atómico en memoria RAM para evitar corrupción de datos
    INDICE_CONOCIMIENTO[ruta_archivo] = nuevos_fragmentos
    print(f"[INDEX] {len(nuevos_fragmentos)} filas cargadas con éxito en RAM desde {ruta_archivo}.")
