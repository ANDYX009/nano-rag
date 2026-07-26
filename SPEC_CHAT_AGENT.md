# SPEC_CHAT_AGENT.md - ESPECIFICACIÓN TÉCNICA DE CONTRATO

## 1. Stack Tecnológico Estricto (Límites Duros)
- **Lenguaje/Runtime:** Python 3.14.4 (Librería Estándar únicamente).
- **Prohibiciones:** Cero uso de `pip`, `virtualenv`, LangChain o bases vectoriales de terceros.
- **Entorno de Red:** Servidor TCP asíncrono nativo implementado mediante `asyncio.start_server`.
- **Concurrencia:** `asyncio` para orquestación, interfaz y manejo de sockets; `asyncio.to_thread` reservado para llamadas bloqueantes de red e interfaces de disco.
- **Plataforma de Despliegue:** Render Cloud Services (Entorno Docker Web Service nativo, operativo detrás de Cloudflare).

## 2. Contrato del Módulo Watcher Dinámico
- **Directorio Objetivo:** Monitoreo dinámico continuo sobre toda la carpeta `knowledge/`.
- **Estrategia Binaria:** Escaneo asíncrono de archivos y lectura obligatoria en bloques fijos de 4096 bytes mediante `while chunk := file.read(4096)`.
- **Validación de Cambio:** Cálculo continuo de hashes SHA-256 almacenados en un diccionario indexado para interceptar mutaciones bit por bit por cada archivo de forma independiente.
- **Asincronía Segura:** El Watcher corre de manera perpetua en una corrutina independiente delegando la carga bloqueante de E/S a hilos con `asyncio.to_thread`.

## 3. Estructura del Índice Dinámico en RAM
- **Formato Soportado:** Archivos estructurados en formato CSV procesados nativamente con el módulo `csv`.
- **Estructura del Estado:** Diccionario global bidimensional en RAM (`INDICE_CONOCIMIENTO`) indexado por la ruta física del archivo como llave maestra.
- **Mapeo Polimórfico de Datos:** Normalización dinámica de columnas al vuelo. Los esquemas clínicos o comerciales se unifican bajo las claves explícitas `'categoria'`, `'palabras_clave'` y `'respuesta_oficial'`.
- **Protección Concurrente:** Acceso exclusivo a memoria RAM protegido mediante un candado asíncrono (`asyncio.Lock`) para evitar condiciones de carrera (*Race Conditions*) durante recargas en caliente.

## 4. Pipeline del Chat y Seguridad de Inyección
- **Interceptación de Preguntas:** El servidor HTTP asíncrono recibe la consulta del usuario en formato JSON, limpia el texto y escanea el índice en RAM iterando sobre todos los archivos cargados.
- **Expansión Semántica:** Inclusión de un Tesauro Podológico local para expandir términos médicos hacia sinónimos populares y maximizar la intersección de conjuntos.
- **Inyección Óptima de Contexto:** El contexto extraído de múltiples archivos se consolida y empaqueta rígidamente dentro de etiquetas estructurales (`<contexto>...</contexto>`) antes de ser enviado al prompt final del modelo `llama-3.1-8b-instant` hospedado en GroqCloud.

## 5. Resiliencia de Red y Guardarraíles en Tiempo Real
- **Bypass CORS Nativo:** Estructura de control al inicio de la lectura del búfer que captura el método `OPTIONS` (Preflight) del navegador, respondiendo de inmediato un estado HTTP `204 No Content` con cabeceras limpias para autorizar el tráfico cruzado de `index.html`.
- **Protección Anticolapsos:** Todo el ciclo de red se encapsula en bloques `try/except Exception` combinados con `await writer.drain()` y cierres en la sección `finally` para garantizar la liberación inmediata de los puertos.
- **Control de Inundación de Memoria:** Validación estricta del encabezado `Content-Length`. Si el tamaño declarado supera el límite duro de 10 Megabytes, el servidor responde con un estado HTTP 413 y aborta la conexión.
- **Mitigación de Lectura Lenta (Slowloris):** Implementación de un **Timeout Absoluto acumulativo** de 3.0 segundos para la lectura completa de cabeceras HTTP.
- **Mecanismo de Inferencia Segura:** Conexión asíncrona hacia la API oficial de **GroqCloud** bajo el formato de autorización Bearer nativo (`Authorization: Bearer gsk_...`) con un motor de **Contingencia Local (Mock Asíncrono)** que intercepta la ausencia del token en desarrollo para simular el procesamiento médico de forma segura.

## 6. Arquitectura de Despliegue en Producción
- **Empaquetado (Containerization):** Manifiesto `Dockerfile` basado en `python:3.14-alpine` con inyección explícita de `ca-certificates` para blindar la seguridad SSL.
- **Control de Puertos Dinámicos:** El servidor asume obligatoriamente el puerto de red mapeado por la variable de entorno `PORT` (por defecto `10000` en Render), prohibiendo el uso de puertos estáticos bloqueados (*hardcoded*).
