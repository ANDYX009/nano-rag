# test_stress.py
import asyncio
import socket
import json

CONFIG = {
    "HOST": "127.0.0.1",
    "PORT": 8000,  # Asegúrate de que coincida con el puerto de tu server.py
}

async def test_slow_attack():
    """Vector 1: Ataque Slowloris. Envia datos extremadamente lento."""
    print("[SLOWLORIS] Iniciando conexión lenta...")
    try:
        reader, writer = await asyncio.open_connection(CONFIG["HOST"], CONFIG["PORT"])
        
        # Enviamos la primera línea del encabezado
        writer.write(b"POST /chat HTTP/1.1\r\n")
        await writer.drain()
        
        print("[SLOWLORIS] Encabezado inicial enviado. Goteando bytes cada 1.5s...")
        # Goteamos bytes para intentar mantener la conexión abierta maliciosamente
        for i in range(3):
            await asyncio.sleep(1.5)
            writer.write(b"X-Dummy-Header: slow\r\n")
            await writer.drain()
            print(f"[SLOWLORIS] Goteo {i+1} enviado...")
            
        # Si llegamos aquí sin excepción, el guardarraíl de 3s falló
        print("[🔴 ALERTA] Slowloris evadió el timeout del servidor.")
        writer.close()
        await writer.wait_closed()
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        print("[🟢 OK] El servidor cortó la conexión lenta exitosamente (Timeout activado).")
    except Exception as e:
        print(f"[⚠️ INFO] Conexión lenta terminada por: {type(e).__name__}")

async def test_flood_attack():
    """Vector 2: Bomba de RAM. Declara un Content-Length gigante (>10MB)."""
    print("[FLOOD] Iniciando bomba de RAM...")
    try:
        reader, writer = await asyncio.open_connection(CONFIG["HOST"], CONFIG["PORT"])
        
        # Declaramos intencionalmente un tamaño de 15 Megabytes
        payload_falso_size = 15 * 1024 * 1024
        headers = (
            f"POST /chat HTTP/1.1\r\n"
            f"Host: {CONFIG['HOST']}\r\n"
            f"Content-Length: {payload_falso_size}\r\n"
            f"Content-Type: application/json\r\n\r\n"
        )
        
        writer.write(headers.encode("utf-8"))
        await writer.drain()
        
        # Leemos la respuesta inmediata del servidor
        respuesta = await reader.read(1024)
        respuesta_txt = respuesta.decode("utf-8", errors="ignore")
        
        if "413" in respuesta_txt or "Payload Too Large" in respuesta_txt:
            print("[🟢 OK] El servidor rechazó la inundación inmediatamente con HTTP 413.")
        else:
            print(f"[🔴 ALERTA] El servidor no rechazó el tamaño masivo. Respuesta: {respuesta_txt[:50]}")
            
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"[🔴 ERROR] Falló la prueba de inundación: {e}")

async def test_happy_path():
    """Vector 3: Flujo Feliz. Petición legítima con término médico del Tesauro."""
    print("[HAPPY PATH] Enviando consulta válida de podología...")
    try:
        reader, writer = await asyncio.open_connection(CONFIG["HOST"], CONFIG["PORT"])
        
        cuerpo = json.dumps({"pregunta": "Tengo onicocriptosis dolorosa"})
        cuerpo_bytes = cuerpo.encode("utf-8")
        
        headers = (
            f"POST /chat HTTP/1.1\r\n"
            f"Host: {CONFIG['HOST']}\r\n"
            f"Content-Length: {len(cuerpo_bytes)}\r\n"
            f"Content-Type: application/json\r\n\r\n"
        )
        
        writer.write(headers.encode("utf-8") + cuerpo_bytes)
        await writer.drain()
        
        respuesta = await reader.read(4096)
        respuesta_txt = respuesta.decode("utf-8", errors="ignore")
        
        if "200 OK" in respuesta_txt:
            print("[🟢 OK] El servidor respondió exitosamente (HTTP 200).")
            # Extraemos la sección del JSON para verificar el deslinde legal
            if "DESLINDE LEGAL" in respuesta_txt or "médico" in respuesta_txt.lower():
                print("[🟢 OK] La respuesta del LLM incluye los guardarraíles médicos.")
            else:
                print("[⚠️ ADVERTENCIA] Respuesta recibida pero sin deslinde legal acotado.")
        else:
            print(f"[🔴 ALERTA] Flujo feliz devolvió error: {respuesta_txt[:100]}")
            
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"[🔴 ERROR] Falló el flujo feliz: {e}")

async def main():
    print("====================================================")
    print("🚀 EJECUTANDO ARNÉS DE PRUEBAS DE RED - NANO-RAG")
    print("====================================================")
    
    # El Orquestador ejecuta los 3 vectores de forma estrictamente concurrente
    await asyncio.gather(
        test_slow_attack(),
        test_flood_attack(),
        test_happy_path()
    )
    
    print("====================================================")
    print("🏁 AUDITORÍA CONCURRENTE FINALIZADA")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(main())
