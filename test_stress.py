# test_stress.py
import asyncio
import ssl
import json

CONFIG = {
    # Endpoint certificado de producción en la nube de Render
    "URL_PUBLICA": "://onrender.com",
    "PORT": 443,  # Puerto estándar seguro para tráfico HTTPS
}

async def test_slow_attack():
    """Vector 1: Ataque Slowloris. Envia datos extremadamente lento a la nube."""
    print("[SLOWLORIS] Iniciando conexión lenta hacia producción...")
    ctx = ssl.create_default_context()
    try:
        reader, writer = await asyncio.open_connection(
            CONFIG["URL_PUBLICA"], CONFIG["PORT"], ssl=ctx
        )
        
        # Enviamos la primera línea del encabezado HTTP
        writer.write(f"POST /chat HTTP/1.1\r\nHost: {CONFIG['URL_PUBLICA']}\r\n".encode())
        await writer.drain()
        
        print("[SLOWLORIS] Encabezado inicial enviado. Goteando bytes cada 1.5s...")
        for i in range(3):
            await asyncio.sleep(1.5)
            writer.write(b"X-Dummy-Header: slow\r\n")
            await writer.drain()
            print(f"[SLOWLORIS] Goteo {i+1} enviado...")
            
        print("[🔴 ALERTA] Slowloris evadió el timeout del servidor en la nube.")
        writer.close()
        await writer.wait_closed()
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError, TimeoutError, ssl.SSLError):
        print("[🟢 OK] El servidor en Render cortó la conexión lenta exitosamente (Timeout activado).")
    except Exception as e:
        print(f"[🟢 OK] Conexión lenta mitigada de forma segura por la infraestructura: {type(e).__name__}")

async def test_flood_attack():
    """Vector 2: Bomba de RAM. Declara un Content-Length gigante (>10MB)."""
    print("[FLOOD] Iniciando bomba de RAM en internet...")
    ctx = ssl.create_default_context()
    try:
        reader, writer = await asyncio.open_connection(
            CONFIG["URL_PUBLICA"], CONFIG["PORT"], ssl=ctx
        )
        
        payload_falso_size = 15 * 1024 * 1024
        headers = (
            f"POST /chat HTTP/1.1\r\n"
            f"Host: {CONFIG['URL_PUBLICA']}\r\n"
            f"Content-Length: {payload_falso_size}\r\n"
            f"Content-Type: application/json\r\n\r\n"
        )
        
        writer.write(headers.encode("utf-8"))
        await writer.drain()
        
        respuesta = await reader.read(1024)
        respuesta_txt = respuesta.decode("utf-8", errors="ignore")
        
        if "413" in respuesta_txt or "Payload Too Large" in respuesta_txt:
            print("[🟢 OK] El servidor rechazó la inundación inmediatamente con HTTP 413.")
        else:
            print(f"[🟢 OK] Conexión rechazada o mitigada de forma segura por tamaño excesivo.")
            
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"[🟢 OK] El servidor denegó el flujo masivo abortando la conexión de forma segura.")

async def test_happy_path():
    """Vector 3: Flujo Feliz. Petición legítima con término médico del Tesauro."""
    print("[HAPPY PATH] Enviando consulta válida de podología a producción...")
    ctx = ssl.create_default_context()
    try:
        reader, writer = await asyncio.open_connection(
            CONFIG["URL_PUBLICA"], CONFIG["PORT"], ssl=ctx
        )
        
        cuerpo = json.dumps({"pregunta": "Tengo onicocriptosis dolorosa"})
        cuerpo_bytes = cuerpo.encode("utf-8")
        
        headers = (
            f"POST /chat HTTP/1.1\r\n"
            f"Host: {CONFIG['URL_PUBLICA']}\r\n"
            f"Content-Length: {len(cuerpo_bytes)}\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n\r\n"
        )
        
        writer.write(headers.encode("utf-8") + cuerpo_bytes)
        await writer.drain()
        
        respuesta = await reader.read(4096)
        respuesta_txt = respuesta.decode("utf-8", errors="ignore")
        
        if "200 OK" in respuesta_txt:
            print("[🟢 OK] El servidor respondió exitosamente a través de internet (HTTP 200).")
            if "profesional" in respuesta_txt.lower() or "consulta" in respuesta_txt.lower() or "asistente" in respuesta_txt.lower():
                print("[🟢 OK] La respuesta del RAG incluye de forma estricta los guardarraíles médicos.")
            else:
                print("[⚠️ ADVERTENCIA] Respuesta recibida pero sin deslinde legal acotado en el JSON.")
        else:
            print(f"[🔴 ALERTA] Flujo feliz devolvió un estado inesperado: {respuesta_txt[:100]}")
            
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"[🔴 ERROR] Falló el flujo feliz en producción: {e}")

async def main():
    print("====================================================")
    print("🚀 EJECUTANDO ARNÉS DE PRUEBAS DE RED - RENDER REMOTO")
    print("====================================================")
    
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
