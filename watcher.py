import asyncio
import hashlib
import os
from indexador import cargar_csv_en_ram

async def calcular_hash_async(ruta_archivo: str) -> str:
    """Calcula el hash SHA-256 de un archivo en bloques fijos de 4096 bytes de forma asíncrona."""
    sha256 = hashlib.sha256()
    
    def leer_bloques():
        with open(ruta_archivo, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()

    return await asyncio.to_thread(leer_bloques)

async def monitorear_directorio(directorio: str):
    """Monitorea continuamente los archivos en el directorio especificado."""
    print(f"Iniciando monitoreo asíncrono en: {directorio}...")
    archivo_monitoreado = os.path.join(directorio, "podologia_faq.csv")
    ultimo_hash = ""

    while True:
        if await asyncio.to_thread(os.path.exists, archivo_monitoreado):
            hash_actual = await calcular_hash_async(archivo_monitoreado)
            
            if hash_actual != ultimo_hash:
                print(f"[RELOAD] Cambio detectado en {archivo_monitoreado}. Actualizando índice en RAM...")
                ultimo_hash = hash_actual
                # Conexión atómica: Cargamos los datos frescos en memoria
                cargar_csv_en_ram(archivo_monitoreado)
        
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitorear_directorio("knowledge"))
    except KeyboardInterrupt:
        print("\nWatcher de podología detenido de forma segura por el usuario.")
