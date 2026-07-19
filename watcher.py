import asyncio
import hashlib
import os
import sys
from indexador import cargar_csv_en_ram

async def calcular_hash_async(ruta_archivo: str) -> str:
    """Calcula el hash SHA-256 de un archivo en bloques fijos de forma asíncrona."""
    sha256 = hashlib.sha256()
    
    def leer_bloques():
        with open(ruta_archivo, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()

    return await asyncio.to_thread(leer_bloques)

async def iniciar_file_watcher(indice_conocimiento: dict, lock_indice: asyncio.Lock, directorio: str = "knowledge") -> None:
    """Monitorea continuamente el CSV inyectando los datos directamente en el índice global."""
    print(f"[WATCHER] Iniciando monitoreo asíncrono seguro en: {directorio}...")
    archivo_monitoreado = os.path.join(directorio, "podologia_faq.csv")
    ultimo_hash = ""

    try:
        while True:
            if await asyncio.to_thread(os.path.exists, archivo_monitoreado):
                hash_actual = await calcular_hash_async(archivo_monitoreado)
                
                if hash_actual != ultimo_hash:
                    print(f"[RELOAD] Cambio detectado en {archivo_monitoreado}. Adquiriendo candado...")
                    
                    async with lock_indice:
                        datos_frescos = cargar_csv_en_ram(archivo_monitoreado)
                        indice_conocimiento.clear()
                        if isinstance(datos_frescos, dict):
                            indice_conocimiento.update(datos_frescos)
                    
                    ultimo_hash = hash_actual
                    print("[RELOAD] Índice global en RAM actualizado con éxito.")

            await asyncio.sleep(5)
    except asyncio.CancelledError:
        print("[INFO] File Watcher detenido limpiamente.")
    except Exception as e:
        print(f"[ERROR CRÍTICO] Falla catastrófica en el File Watcher: {e}", file=sys.stderr)
        raise
