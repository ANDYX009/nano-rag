import asyncio
import json
import urllib.request
import logging
import os
import sys
import buscador


# Configuración estricta del sistema de logs nativo para producción
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
# Guardarraíles duros de seguridad definidos en el contrato técnico
MAX_BYTES_CUERPO = 10 * 1024 * 1024  # Límite estricto de 10 Megabytes
TIMEOUT_RED_SEGUNDOS = 3.0           # Mitigación contra ataques Slowloris

async def manejador_cliente(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
):
    """Gestiona de forma asíncrona y aislada el ciclo de vida de cada socket."""
    direccion_cliente = writer.get_extra_info('peername')
    logging.info(
        f"Nueva conexión entrante desde: {direccion_cliente}"
    )

    try:
        # Aquí inicia el aislamiento total del procesamiento de la petición
        # 1. Lectura de cabeceras HTTP protegida por límite de tiempo
        datos_cabeceras = b""
        while b"\r\n\r\n" not in datos_cabeceras:
            # Lee fragmentos del flujo de red de forma asíncrona y segura
            fragmento = await asyncio.wait_for(
                reader.read(4096),
                timeout=TIMEOUT_RED_SEGUNDOS
            )
            if not fragmento:
                logging.warning(
                    f"El cliente {direccion_cliente} cerró la conexión abruptamente."
                )
                writer.close()
                return
            datos_cabeceras += fragmento
        # 2. Separar cabeceras y buscar el tamaño declarado del cuerpo
        bloque_cabeceras, _ = datos_cabeceras.split(b"\r\n\r\n", 1)
        texto_cabeceras = bloque_cabeceras.decode("utf-8", errors="ignore")

        tamano_cuerpo = 0
        for linea in texto_cabeceras.split("\r\n"):
            if linea.lower().startswith("content-length:"):
                try:
                    tamano_cuerpo = int(linea.split(":", 1)[1].strip())
                except ValueError:
                    logging.warning(
                        f"Content-Length inválido desde {direccion_cliente}"
                    )
                break

        # Aplicación del guardarraíl estricto contra inundación de RAM
        if tamano_cuerpo > MAX_BYTES_CUERPO:
            logging.error(
                f"Petición rechazada: {tamano_cuerpo} bytes superan el límite de 10MB."
            )
            respuesta_error = (
                b"HTTP/1.1 413 Payload Too Large\r\nConnection: close\r\n\r\n"
            )
            writer.write(respuesta_error)
            await writer.drain()
            writer.close()
            return
        # =====================================================================
        # CORRECTO: 3. Leer el cuerpo abstrayendo los bytes ya capturados en RAM
        # =====================================================================
        # Dividimos en dos partes: cabeceras (índice 0) y fragmento del cuerpo (índice 1)
        partes_peticion = datos_cabeceras.split(b"\r\n\r\n", 1)
        fragmento_cuerpo = partes_peticion[1]
        
        bytes_restantes_por_leer = tamano_cuerpo - len(fragmento_cuerpo)

        if bytes_restantes_por_leer > 0:
            # Vamos a la red únicamente por el fragmento faltante
            bytes_faltantes = await asyncio.wait_for(
                reader.readexactly(bytes_restantes_por_leer),
                timeout=TIMEOUT_RED_SEGUNDOS
            )
            bytes_cuerpo = fragmento_cuerpo + bytes_faltantes
        else:
            # El cuerpo completo ya venía en el primer paquete de red
            bytes_cuerpo = fragmento_cuerpo[:tamano_cuerpo]
            texto_cuerpo = bytes_cuerpo.decode("utf-8")
            # Carga del payload JSON validando que no esté malformado
        datos_json = json.loads(texto_cuerpo)
        pregunta_usuario = datos_json.get("pregunta", "").strip()

        if not pregunta_usuario:
            raise ValueError(
                "El campo 'pregunta' está vacío o ausente en el JSON."
            )

        logging.info(
            f"Pregunta recibida con éxito: '{pregunta_usuario[:30]}...'"
        )

        # =====================================================================

        # 4. Invocación al motor de búsqueda local con el Tesauro integrado
        # Escanea el índice dinámico en RAM en busca de las filas más relevantes
        # Añadimos la ruta del conocimiento como argumento requerido por la función
        filas_coincidentes = buscador.buscar_fragmento_relevante(
            pregunta_usuario, "knowledge/podologia_faq.csv"
        )


        # Empaquetado estricto del contexto para mitigar la inyección de prompts
        contexto_medico = ""
        if filas_coincidentes:
            contexto_medico = "\n".join([
                f"Pregunta frecuente: {f['pregunta']}"
                f"\nRespuesta médica: {f['respuesta']}"
                for f in filas_coincidentes
            ])

        prompt_final = (
            "<contexto>\n"
            f"{contexto_medico or 'No hay información específica en el índice.'}\n"
            "</contexto>\n\n"
            f"Pregunta del paciente: {pregunta_usuario}"
        )


        # 5. Extracción segura de credenciales mediante variables de entorno nativas
        url_api = os.environ.get("API_URL_LLM", "https://router.huggingface.co/v1/chat/completions")
        token_api = os.environ.get("API_TOKEN_LLM", "Bearer free")


        # Encabezado de autenticación estándar

        headers_api = {
            "Authorization": token_api,  # Token ficticio formateado correcto
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NanoRAG/1.0"
        }


         # Construcción del payload nativo compatible con la API de Inferencia directa de Hugging Face
        payload_api = json.dumps({
            "inputs": (
                f"Eres un asistente virtual de podología médica. Responde de forma breve (máximo 150 palabras) "
                f"usando solo el contexto provisto. Al final de tu respuesta agrega obligatoriamente la nota de deslinde.\n\n"
                f"{prompt_final}\n\n"
                f"*Nota: Esta es una guía informativa y no reemplaza la consulta con un podólogo profesional.*"
            ),
            "parameters": {
                "temperature": 0.3,
                "max_new_tokens": 250
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            url_api, data=payload_api, headers=headers_api, method="POST"
        )

        # Se ejecuta la llamada bloqueante en un hilo secundario para no congelar la red
        response_api = await asyncio.to_thread(
            urllib.request.urlopen, req, timeout=10.0
        )
        
        # El formato de respuesta directa de Hugging Face devuelve una lista de diccionarios con 'generated_text'
        datos_api = json.loads(response_api.read().decode("utf-8"))
        texto_llm = datos_api[0]["generated_text"].strip()

        # 6. Serialización del JSON de salida y cálculo de tamaño real
        payload_respuesta = json.dumps({"respuesta": texto_llm}).encode("utf-8")

        # Redacción de cabeceras oficiales HTTP/1.1 para la respuesta
        cabeceras_respuesta = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(payload_respuesta)}\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("utf-8")

        # Inyección en el búfer de red y expulsión física de bytes
        writer.write(cabeceras_respuesta + payload_respuesta)
        await writer.drain()  # Espera pacientemente a que se vacíe el búfer

    except Exception as error_critico:
        logging.error(
            f"Fallo general en la conexión con {direccion_cliente}: {error_critico}"
        )

    finally:
        # Cierre definitivo y limpio del socket de red pase lo que pase
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        logging.info(
            f"Conexión con {direccion_cliente} liberada y cerrada."
        )


async def main():
    """Inicializa el servidor TCP asíncrono en el bucle de eventos principal."""
    host = "0.0.0.0"  # Escucha en todas las interfaces de red (Producción/WSL)
    puerto = 8000

    # Levanta el servidor apuntando al manejador de clientes
    servidor = await asyncio.start_server(manejador_cliente, host, puerto)

    logging.info(f"=== SERVIDOR NANO-RAG ASÍNCRONO INICIADO ===")
    logging.info(f"Escuchando peticiones HTTP en http://{host}:{puerto}/chat")

    # Mantiene el servidor corriendo de forma perpetua e indefinida
    async with servidor:
        await servidor.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Servidor detenido de forma voluntaria por el usuario.")
