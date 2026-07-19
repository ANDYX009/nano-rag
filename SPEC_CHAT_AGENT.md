# SPEC_CHAT_AGENT.md - ESPECIFICACIÓN TÉCNICA DE CONTRATO

## 1. Stack Tecnológico Estricto (Límites Duros)
- **Lenguaje/Runtime:** Python 3.14.4 (Librería Estándar únicamente).
- **Prohibiciones:** Cero uso de `pip`, `virtualenv`, LangChain o bases vectoriales de terceros.
- **Entorno de Red:** Servidor TCP asíncrono nativo implementado mediante `asyncio.start_server`.
- **Concurrencia:** `asyncio` para orquestación, interfaz y manejo de sockets; `asyncio.to_thread` reservado para llamadas bloqueantes de red en `urllib.request`.
- **Plataforma de Despliegue:** Hugging Face Spaces (Entorno Docker Blank nativo, Capa Gratuita Perpetua 24/7).

## 2. Contrato del Módulo Watcher Dinámico
- **Directorio Objetivo:** Monitoreo estricto sobre la carpeta `knowledge/`.
- **Estrategia Binaria:** Lectura obligatoria en bloques fijos de 4096 bytes mediante `while chunk := file.read(4096)`.
- **Validación de Cambio:** Cálculo continuo de hashes SHA-256 para interceptar mutaciones bit por bit de manera exacta.
- **Asincronía Segura:** El Watcher corre de manera perpetua en una corrutina asíncrona independiente. Toda lectura de disco se delega a hilos con `asyncio.to_thread`.

## 3. Estructura del Índice Dinámico en RAM
- **Formato Soportado:** Archivos estructurados en formato CSV procesados nativamente con el módulo `csv`.
- **Estructura del Estado:** Diccionario global en RAM (`INDICE_CONOCIMIENTO`) que almacena la estructura del CSV de forma atómica.
- **Mapeo de Datos:** Cada fila del CSV se normaliza con claves explícitas (`categoria`, `palabras_clave`, `pregunta`, `respuesta`) alineadas al motor de búsqueda.
- **Protección Concurrente:** Acceso exclusivo a memoria RAM protegido mediante un candado asíncrono (`asyncio.Lock`) para evitar condiciones de carrera (*Race Conditions*) durante recargas en caliente.

## 4. Pipeline del Chat y Seguridad de Inyección
- **Interceptación de Preguntas:** El servidor HTTP asíncrono recibe la consulta del usuario en formato JSON, limpia el texto y escanea el índice en RAM mediante el motor léxico.
- **Expansión Semántica:** Inclusión de un Tesauro Podológico local para expandir términos médicos hacia sinónimos populares y maximizar la intersección de conjuntos.
- **Inyección Óptima de Contexto:** El contexto extraído se empaqueta rígidamente dentro de etiquetas estructurales (`<contexto>...</contexto>`) antes de ser enviado al prompt final, limitando la respuesta del LLM a 150 palabras y forzando una leyenda de deslinde legal.

## 5. Resiliencia de Red y Guardarraíles en Tiempo Real
- **Protección Anticolapsos:** Todo el ciclo de red se encapsula en bloques `try/except Exception` combinados con `await writer.drain()` y cierres en la sección `finally` para garantizar que conexiones corruptas no tumben el proceso.
- **Control de Inundación de Memoria:** Validación estricta del encabezado `Content-Length`. Si el tamaño declarado supera el límite duro de 10 Megabytes, el servidor responde con un estado HTTP 413 y aborta la conexión para proteger la RAM.
- **Mitigación de Lectura Lenta (Slowloris):** Implementación de un **Timeout Absoluto acumulativo** de 3.0 segundos calculando la ventana de tiempo decreciente mediante el lazo de eventos para neutralizar ataques de goteo de bytes.
- **Mecanismo de Inferencia Segura:** Conexión asíncrona hacia la API de Inferencia de Hugging Face. Incluye un motor de **Contingencia Local (Mock Asíncrono)** que intercepta la credencial de desarrollo para simular el procesamiento médico sin colapsar por bloqueos de red externos.

## 6. Arquitectura de Despliegue en Producción
- **Empaquetado (Containerization):** Archivo de manifiesto de construcción `Dockerfile` basado en `python:3.14-alpine` para garantizar un entorno inmutable, ligero y seguro de ejecución.
- **Control de Puertos Dinámicos:** El servidor asume obligatoriamente el puerto de red mapeado por la variable de entorno `PORT` (por defecto `7860` en Hugging Face Spaces), prohibiendo el uso de puertos estáticos bloqueados (*hardcoded*).

---

# CONTEXTO_SESION.md - PUNTO DE PARTIDA NANO-RAG

## 🤖 1. Posicionamiento del Tutor y Guardarraíles de Trabajo
- **Rol Activo:** Tutor Avanzado de Software, Redes e Ingeniería de Datos (Estricto Python 3.14.4 Standard).
- **Control de Flujo:** Ejecutar y planificar **una sola tarea atómica a la vez**. Esperar palabra clave **"listo"**.
- **Restricciones:** Respuestas compactas (10 a 15 renglones), cero invención, priorizar planeación antes de generar.

## 🚀 2. Estado del Repositorio y Punto Exacto de Partida
- **Capa de Red (`server.py`):** 100% funcional y blindada. Parser de bytes manual optimizado para leer el cuerpo combinando RAM intermedio y red de forma asíncrona.
- **Arnés de Pruebas (`test_stress.py`):** 100% funcional. Valida bomba de RAM y Slowloris concurrentemente en Warp.
- **Sincronización:** Repositorio local limpio y listo para el hito de infraestructura.

## 📂 3. Estructura de Carpetas Actual del Repositorio
```text
~/proyectos/nano-rag/         <-- Sistema Ext4 nativo de Linux (WSL)
├── SPEC_CHAT_AGENT.md         <-- Contrato técnico y guardarraíles del diseño (Actualizado HF).
├── CONTEXTO_SESION.md         <-- Resumen de restauración e higiene de contexto (Actualizado HF).
├── app.py                     <-- Orquestador maestro central del sistema asíncrono.
├── server.py                  <-- Servidor HTTP puro con blindaje Slowloris y Bomba RAM.
├── watcher.py                 <-- Corrutina asíncrona de monitoreo de archivos.
├── indexador.py               <-- Extractor utilitario de datos estructurados CSV.
├── buscador.py                <-- Motor léxico desacoplado con expansión de sinónimos.
├── test_stress.py             <-- Arnés concurrente de estrés y auditoría de red local.
└── knowledge/                 <-- Frontera aislada de datos del conocimiento.
    └── podologia_faq.csv      <-- Base de conocimiento estructurada de la clínica.
```

## 🚀 4. Punto Exacto de Partida para la Siguiente Sesión
El sistema actual procesa, vigila e identifica perfectamente en memoria RAM la información médica ante cualquier cambio físico de datos. Nos quedamos exactamente en el umbral del **Día 1 del Plan de Despliegue en la Nube (SDD)**.

---

# PLAN_DESPLIEGUE_SDD.md - PLAN MAESTRO DE DESPLIEGUE EN LA NUBE (SDD - HUGGING FACE SPACES)

## 🕒 DÍA 1: Manifiestos de Contenedorización e Inyección Dinámica

### 📌 Paso 1.1: Adaptación de la Firma de Red en el Servidor
- **Especificación (Spec):** Modificar la función `iniciar_servidor_http` de `server.py` para leer el puerto de red a través de la variable de entorno `PORT`, asignando `7860` por defecto para garantizar compatibilidad con Hugging Face.
- **Prueba de Verificación:** Compilar estáticamente el archivo modificado y asegurar que no existan errores léxicos: `python3 -m py_compile server.py`
- **🛑 CLÁUSULA DURA:** Prohibido avanzar al paso 1.2 hasta que `server.py` sea sintácticamente válido y lea de forma dinámica el puerto de la nube.

### 📌 Paso 1.2: Creación del Manifiesto de Despliegue (`Dockerfile`)
- **Especificación (Spec):** Diseñar un archivo plano sin extensión llamado `Dockerfile` en la raíz utilizando `python:3.14-alpine`, exponiendo el puerto `7860` e inyectando las directivas básicas del sistema.
- **Prueba de Verificación:** Validar la existencia física del manifiesto de configuración en la raíz del espacio de trabajo mediante el comando de terminal: `cat Dockerfile`
- **🛑 CLÁUSULA DURA:** Prohibido avanzar al paso 1.3 hasta que el archivo `Dockerfile` contenga la estructura exacta del contrato técnico.

### 📌 Paso 1.3: Consolidación Documental y Envío a GitHub
- **Especificación (Spec):** Realizar el commit y empuje (*push*) exclusivo de los archivos de documentación actualizados (`SPEC_CHAT_AGENT.md`, `CONTEXTO_SESION.md`, `PLAN_DESPLIEGUE_SDD.md`) y el nuevo `Dockerfile` hacia el origen remoto `main`.
- **Prueba de Verificación:** Verificar a través del panel web de GitHub que el repositorio remoto muestre los mismos archivos y los commits sincronizados.
- **🛑 CLÁUSULA DURA:** Prohibido avanzar al Día 2 si el repositorio remoto en la nube no se encuentra exactamente en el mismo estado físico que tu área de trabajo local.

## 🕒 DÍA 2: Vinculación Autónoma y Auditoría de Tráfico Remoto

### 📌 Paso 2.1: Creación del Espacio (Space) en Hugging Face
- **Especificación (Spec):** Crear un nuevo Space en tu panel de Hugging Face. Parámetros mandatorios: *SDK:* **Docker**, *Template:* **Blank**, *Visibility:* **Public**.
- **Prueba de Verificación:** Acceder al espacio recién creado en la interfaz del navegador y verificar que muestre el estado inicial `No files yet` o listo para recibir el código.
- **🛑 CLÁUSULA DURA:** Prohibido avanzar al paso 2.2 hasta que el Space esté instanciado con el motor de Docker Blank seleccionado de forma correcta.

### 📌 Paso 2.2: Vinculación por Repositorio Remoto (Git Mirroring)
- **Especificación (Spec):** Conectar tu repositorio de GitHub para que clone automáticamente la suite dentro del Space de Hugging Face o añadir el origen remoto de Hugging Face mediante terminal para empujar el código.
- **Prueba de Verificación:** El visor de Logs en tiempo real de Hugging Face Spaces debe mostrar la fase de construcción (*Building*) en verde y pasar a estado `Running`, imprimiendo el arranque del orquestador:
```text
[INFO] Iniciando Orquestador Central Nano-RAG...
[WATCHER] Iniciando monitoreo asíncrono seguro en: knowledge...
[SERVIDOR] Escuchando en http://127.0.0.1:7860
```
- **🛑 CLÁUSULA DURA:** Prohibido avanzar al paso 2.3 si el contenedor de Hugging Face arroja un error de compilación de Docker o falla en la inicialización asíncrona.

### 📌 Paso 2.3: Auditoría Concurrente Cruzando Internet (Hito 100%)
