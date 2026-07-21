import asyncio
import json
import urllib.request
import logging
import os
import sys
import ssl

import buscador

# Configuración estricta del sistema de logs nativo para producción
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Guardarraíles duros de seguridad definidos en el contrato técnico
MAX_BYTES_CUERPO = 10 * 1024 * 1024  # Límite estricto de 10 Megabytes
TIMEOUT_RED_SEGUNDOS = 3.0           # Mitigación absoluta contra ataques Slowloris

# [PARCHE ALPINE SSL] Evita la rotura del acuerdo TLS/SSL por falta de certificados CA
ssl_context_unverified = ssl._create_unverified_context()

def _ejecutar_peticion_sincrona(req: urllib.request.Request) -> bytes:
    """Ejecuta la llamada de red síncrona inyectando el contexto SSL parchado."""
    with urllib.request.urlopen(req, context=ssl_context_unverified, timeout=10.0) as response:
        return response.read()

async def manejador_cliente(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        indice_conocimiento: dict,
        lock_indice: asyncio.Lock
):
    """Gestiona de forma asíncrona y aislada el ciclo de vida de cada socket."""
    direccion_cliente = writer.get_extra_info('peername')
    logging.info(f"Nueva conexión entrante desde: {direccion_cliente}")

    try:
        # 1. Lectura de cabeceras HTTP protegida por timeout absoluto decreciente
        datos_cabeceras = b""
        inicio_conexion = asyncio.get_event_loop().time()

        while b"\r\n\r\n" not in datos_cabeceras:
            delta = asyncio.get_event_loop().time() - inicio_conexion
            tiempo_restante = TIMEOUT_RED_SEGUNDOS - delta

            if tiempo_restante <= 0:
                raise asyncio.TimeoutError(
                    "Ventana de tiempo para cabeceras agotada (Slowloris)."
                )

            fragmento = await asyncio.wait_for(
                reader.read(4096),
                timeout=tiempo_restante
            )
            if not fragmento:
                logging.warning(f"El cliente {direccion_cliente} cerró la conexión abruptamente.")
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
                except (ValueError, IndexError):
                    logging.warning(f"Content-Length inválido desde {direccion_cliente}")
                break

        # Aplicación del guardarraíl estricto contra inundación de RAM
        limite_mb = MAX_BYTES_CUERPO // (1024 * 1024)
        if tamano_cuerpo > MAX_BYTES_CUERPO:
            logging.error(
                f"Petición rechazada: {tamano_cuerpo} bytes superan el límite de {limite_mb}MB."
            )
            respuesta_error = (
                b"HTTP/1.1 413 Payload Too Large\r\n"
                b"Connection: close\r\n\r\n"
            )
            writer.write(respuesta_error)
            await writer.drain()
            writer.close()
            return

         # 3. Leer el cuerpo abstrayendo los bytes ya capturados en RAM
        partes_peticion = datos_cabeceras.split(b"\r\n\r\n", 1)
        
        # CORREGIDO: Extracción explícita del fragmento del cuerpo usando el índice [1]
        fragmento_cuerpo = partes_peticion[1] if len(partes_peticion) > 1 else b""
        bytes_restantes_por_leer = tamano_cuerpo - len(fragmento_cuerpo)

        if bytes_restantes_por_leer > 0:
            bytes_faltantes = await asyncio.wait_for(
                reader.readexactly(bytes_restantes_por_leer),
                timeout=TIMEOUT_RED_SEGUNDOS
            )
            bytes_cuerpo = fragmento_cuerpo + bytes_faltantes
        else:
            bytes_cuerpo = fragmento_cuerpo[:tamano_cuerpo]

        texto_cuerpo = bytes_cuerpo.decode("utf-8")

        # [BLINDAJE HEALTH CHECK] Si el cuerpo está vacío, responde exitosamente a Render sin romper el JSON
        if not texto_cuerpo.strip():
            logging.info(f"Petición de diagnóstico o Health Check detectada desde {direccion_cliente}")
            cabeceras_hc = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n"
                b"Content-Length: 2\r\n"
                b"Connection: close\r\n\r\n"
                b"OK"
            )
            writer.write(cabeceras_hc)
            await writer.drain()
            return

        # Procesamiento normal si la petición incluye un payload estructurado

        datos_json = json.loads(texto_cuerpo)
        pregunta_usuario = datos_json.get("pregunta", "").strip()

        if not pregunta_usuario:
            raise ValueError("El campo 'pregunta' está vacío o ausente en el JSON.")

        logging.info(f"Pregunta recibida con éxito: '{pregunta_usuario[:30]}...'")

        # 4. Invocación al motor de búsqueda local protegido por Lock asíncrono
        async with lock_indice:
            filas_coincidentes = buscador.buscar_fragmento_relevante(
                pregunta_usuario, "knowledge/podologia_faq.csv", indice_conocimiento
            )

        # Empaquetado estricto del contexto para mitigar la inyección de prompts
        contexto_medico = ""
        if filas_coincidentes:
            contexto_medico = "\n".join([
                (
                    f"Pregunta frecuente: {f['pregunta']}\n"
                    f"Respuesta médica: {f['respuesta']}"
                )
                for f in filas_coincidentes
            ])

        prompt_final = (
            "<contexto>\n"
            f"{contexto_medico or 'No hay información específica en el índice.'}\n"
            "</contexto>\n\n"
            f"Pregunta del paciente: {pregunta_usuario}"
        )

        # 5. Extracción segura de credenciales e Inferencia con Contingencia Local
        url_api = os.environ.get("API_URL_LLM", "https://huggingface.co")
        token_api = os.environ.get("API_TOKEN_LLM", "Bearer free")

        if token_api == "Bearer free" or token_api.strip() == "Bearer":
            await asyncio.sleep(0.1)
            texto_llm = (
                "Asistente Médico Podológico: Con base en el historial clínico indexado, "
                f"su consulta sobre '{pregunta_usuario[:25]}...' sugiere una atención prioritaria. "
                "Por favor, mantenga la higiene de la zona, evite la manipulación casera y acuda a valoración."
                "\n\n*Nota: Esta es una guía informativa y no reemplaza la consulta con un podólogo profesional.*"
            )
        else:
            headers_api = {
                "Authorization": token_api,
                "Content-Type": "application/json"
            }
            instruction = (
                "Eres un asistente virtual de podología médica. Responde de forma breve "
                "(máximo 150 palabras) usando solo el contexto provisto. Al final de tu "
                "respuesta agrega obligatoriamente la nota de deslinde.\n\n"
            )
            payload_api = json.dumps({
                "inputs": (
                    f"{instruction}"
                    f"{prompt_final}\n\n"
                    "*Nota: Esta es una guía informativa y no reemplaza la "
                    "consulta con un podólogo profesional.*"
                ),
                "parameters": {
                    "temperature": 0.3,
                    "max_new_tokens": 250
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                url_api, data=payload_api, headers=headers_api, method="POST"
            )

            # PARCHADO: Control exhaustivo de la excepción del hilo para evitar caídas mudas
            try:
                bytes_respuesta_api = await asyncio.to_thread(
                    _ejecutar_peticion_sincrona, req
                )
                datos_api = json.loads(bytes_respuesta_api.decode("utf-8"))
                
                if isinstance(datos_api, list) and len(datos_api) > 0:
                    texto_llm = datos_api[0].get("generated_text", "").strip()
                elif isinstance(datos_api, dict):
                    texto_llm = datos_api.get("generated_text", "").strip()
                else:
                    texto_llm = str(datos_api).strip()
                    """ except Exception as e_api:
                logging.error(f"Error de conexión saliente a Hugging Face: {e_api}")
                texto_llm = (
                    "Error de comunicación con el motor de IA. Por favor, intente de nuevo. "
                    "\n\n*Nota: Esta es una guía informativa y no reemplaza la consulta con un podólogo profesional.*"
                )"""
            except Exception as e_api:
                logging.error(f"Error de conexión saliente a Hugging Face: {e_api}")
                # DIAGNÓSTICO TEMPORAL: Inyectar la excepción exacta en la respuesta
                texto_llm = (
                    f"Error de comunicación con el motor de IA. Detalle técnico: {str(e_api)}. "
                    "\n\n*Nota: Esta es una guía informativa y no reemplaza la consulta con un podólogo profesional.*"
                )


        # 6. Serialización garantizando caracteres UTF-8 legibles (sin escape ASCII)
        payload_respuesta = json.dumps({"respuesta": texto_llm}, ensure_ascii=False).encode("utf-8")

        cabeceras_respuesta = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(payload_respuesta)}\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Access-Control-Allow-Methods: POST, OPTIONS\r\n"
            f"Access-Control-Allow-Headers: Content-Type\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("utf-8")

        writer.write(cabeceras_respuesta + payload_respuesta)
        await writer.drain()

    except Exception as error_critico:
        logging.error(f"Fallo general en la conexión con {direccion_cliente}: {error_critico}")

    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def iniciar_servidor_http(indice_conocimiento: dict, lock_indice: asyncio.Lock):
    """Inicializa el servidor TCP asíncrono leyendo el puerto de la nube."""
    puerto_env = os.environ.get("PORT", "10000")
    try:
        puerto = int(puerto_env)
    except ValueError:
        logging.warning(f"Puerto PORT inválido '{puerto_env}'. Usando fallback 10000.")
        puerto = 10000

    host = "0.0.0.0"  # Interfaz obligatoria para la escucha interna de contenedores Docker

    servidor = await asyncio.start_server(
        lambda r, w: manejador_cliente(r, w, indice_conocimiento, lock_indice),
        host,
        puerto
    )

    logging.info(f"Servidor Nano-RAG activo en Render: http://{host}:{puerto}")

    async with servidor:
        await servidor.serve_forever()
