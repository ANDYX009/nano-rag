# SPEC_CHAT_AGENT.md - ESPECIFICACIÓN TÉCNICA DE CONTRATO

## 1. Stack Tecnológico Estricto (Límites Duros)
- **Lenguaje/Runtime:** Python 3.14.4 (Librería Estándar únicamente).
- **Prohibiciones:** Cero uso de `pip`, `virtualenv`, LangChain o bases vectoriales de terceros.
- **Entorno de Red:** Servidor HTTP nativo utilizando `http.server` y `socketserver` integrados.
- **Concurrencia:** `asyncio` para orquestación e interfaz; `asyncio.to_thread` para I/O bloqueante de disco.
- **Plataforma de Despliegue:** Render / Railway (Entorno Linux gestionado).

## 2. Contrato del Módulo Watcher Dinámico
- **Directorio Objetivo:** Monitoreo estricto sobre la carpeta `knowledge/`.
- **Estrategia Binaria:** Lectura obligatoria en bloques fijos de 4096 bytes mediante `while chunk := file.read(4096)`.
- **Validación de Cambio:** Cálculo continuo de hashes SHA-256 para interceptar mutaciones bit por bit de manera exacta.
- **Asincronía Segura:** El Watcher corre de manera perpetua en una corrutina asíncrona independiente. Toda lectura de disco se delega a hilos con `asyncio.to_thread`.

## 3. Estructura del Índice Dinámico en RAM
- **Formato Soportado:** Archivos estructurados en formato CSV procesados nativamente con el módulo `csv`.
- **Estructura del Estado:** Diccionario global en RAM que almacena la firma del archivo (`hash`), marca de tiempo (`timestamp`) y una lista de diccionarios con los fragmentos de texto limpios.
- **Mapeo de Datos:** Cada fila o bloque del CSV contendrá claves explícitas (`fuente`, `contenido_limpio`) para evitar el desbordamiento de la ventana de contexto.
- **Higiene de RAM:** Si el Watcher detecta que un archivo fue eliminado de `knowledge/`, su índice correspondiente es borrado inmediatamente de la memoria RAM usando el operador `del` para liberar espacio físico.

## 4. Pipeline del Chat y Seguridad de Inyección
- **Interceptación de Preguntas:** El servidor HTTP asíncrono recibe la consulta del usuario, limpia el texto y escanea el índice en RAM para extraer las filas CSV más relevantes basándose en la coincidencia exacta de palabras clave.
- **Inyección Óptima de Contexto:** El contexto extraído se empaqueta rígidamente dentro de etiquetas estructurales (ej. `<contexto>...</contexto>`) antes de ser enviado al modelo de inferencia.
- **Aislamiento de Prompts:** Si el archivo CSV o la pregunta del usuario intentan alterar las reglas del sistema mediante instrucciones maliciosas, el parser nativo filtrará los comandos para anular cualquier intento de secuestro de comportamiento (*Prompt Injection*).
