import asyncio
import sys

# BLOQUE 1: Importación de Componentes Reales del Sistema
try:
    from server import iniciar_servidor_http
    from watcher import iniciar_file_watcher
except ImportError as e:
    print(f"[ERROR CRÍTICO] Error de acoplamiento de módulos: {e}", file=sys.stderr)
    sys.exit(1)

# BLOQUE 2: Estado Global Compartido (Estructura de Datos Atómica)
INDICE_CONOCIMIENTO: dict[str, str] = {}
LOCK_INDICE = asyncio.Lock()  # Blindaje total contra Race Conditions

# BLOQUE 3: Orquestador Maestro y Control de Ciclo de Vida
async def main() -> None:
    print("[INFO] Iniciando Orquestador Central Nano-RAG...")
    
    # Instanciación de las corrutinas reales compartiendo el mismo puntero de memoria y candado
    tarea_watcher = asyncio.create_task(iniciar_file_watcher(INDICE_CONOCIMIENTO, LOCK_INDICE, "knowledge"))
    tarea_servidor = asyncio.create_task(iniciar_servidor_http(INDICE_CONOCIMIENTO, LOCK_INDICE))
    
    try:
        # Orquestación concurrente. Si el watcher falla en disco o el servidor en red, el sistema cae coordinadamente
        await asyncio.gather(tarea_watcher, tarea_servidor)
    except Exception as e:
        print(f"[ALERTA SISMICA] Colapso del pipeline detectado: {e}", file=sys.stderr)
    finally:
        # BLOQUE 4: Protocolo de Contingencia y Liberación Inmediata de Sockets
        print("[INFO] Ejecutando protocolo de desmantelamiento seguro y limpieza de red...")
        tarea_watcher.cancel()
        tarea_servidor.cancel()
        # Forzamos la recolección de las cancelaciones para liberar el puerto 8000 en microsegundos
        await asyncio.gather(tarea_watcher, tarea_servidor, return_exceptions=True)
        print("[SISTEMA] Recursos del sistema purgados. Nano-RAG fuera de línea de forma exitosa.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Apagado controlado por señal externa (Ctrl+C).")
