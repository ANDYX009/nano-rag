import asyncio
import hashlib
import os
import sys
import indexador  # Importamos el módulo para leer su estado en RAM de forma limpia

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
    """Monitorea continuamente el directorio inyectando cualquier CSV en el índice global."""
    print(f"[WATCHER] Iniciando monitoreo asíncrono dinámico en: {directorio}...")
    
    # Registro de hashes indexado por el nombre de cada archivo
    estados_hash: dict[str, str] = {}

    try:
        while True:
            if await asyncio.to_thread(os.path.exists, directorio):
                # Listar los archivos del directorio de forma asíncrona
                archivos = await asyncio.to_thread(os.listdir, directorio)
                archivos_csv = [f for f in archivos if f.endswith(".csv")]

                for archivo in archivos_csv:
                    ruta_completa = os.path.join(directorio, archivo)
                    hash_actual = await calcular_hash_async(ruta_completa)
                    ultimo_hash = estados_hash.get(ruta_completa, "")

                    if hash_actual != ultimo_hash:
                        print(f"[RELOAD] Cambio detectado en {ruta_completa}. Adquiriendo candado...")
                        
                        async with lock_indice:
                            # Ejecuta la indexación polimórfica que actualiza la RAM del indexador
                            await asyncio.to_thread(indexador.cargar_csv_en_ram, ruta_completa)
                            
                            # Sincroniza de forma limpia la memoria compartida del orquestador central
                            indice_conocimiento.clear()
                            indice_conocimiento.update(indexador.INDICE_CONOCIMIENTO)
                        
                        estados_hash[ruta_completa] = hash_actual
                        print(f"[RELOAD] Índice global actualizado con éxito desde {archivo}.")

            await asyncio.sleep(5)
    except asyncio.CancelledError:
        print("[INFO] File Watcher detenido limpiamente.")
    except Exception as e:
        print(f"[ERROR CRÍTICO] Falla catastrófica en el File Watcher: {e}", file=sys.stderr)
        raise
