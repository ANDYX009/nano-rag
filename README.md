# 🩻 Nano-RAG: Agente Podológico Asíncrono de Bajo Nivel

## 🎯 Descripción General
Este proyecto consiste en un **Agente de Inteligencia Artificial (RAG)** enfocado en la atención y orientación médica podológica. A diferencia de las arquitecturas tradicionales basadas en frameworks pesados, esta solución fue construida desde los cimientos del sistema utilizando **Python 3.14 Standard**, sockets TCP de bajo nivel y un parser manual de bytes optimizado para alta concurrencia, escalabilidad de conocimiento y seguridad perimetral.

---

## 🏗️ Arquitectura de la Solución
La aplicación opera mediante un modelo de orquestación central asíncrona (`asyncio.gather`) dividida en componentes críticos de red y disco que comparten memoria en RAM:

1. **File Watcher Dinámico y Polimórfico (`watcher.py` / `indexador.py`):** Monitorea continuamente el directorio `knowledge/` mediante hashes criptográficos (SHA-256) en bloques fijos de 4KB. Al detectar mutaciones físicas o la adición de nuevos archivos en caliente, adquiere un candado mutuo (`asyncio.Lock`) y normaliza dinámicamente el esquema de las columnas al vuelo, inyectando los datos de forma limpia en la estructura global compartida de la RAM sin necesidad de reiniciar el proceso.
2. **Servidor HTTP Nativo (`server.py`):** Levanta un socket TCP en la interfaz `0.0.0.0` capaz de recibir peticiones concurrentes cruzando la WAN. Cuenta con blindaje perimetral activo:
   * **Bypass CORS de Bajo Nivel:** Intercepta en la lectura del primer búfer las llamadas Preflight (`OPTIONS`) enviadas por los navegadores modernos, respondiendo de inmediato con un código HTTP `204 No Content` y las cabeceras `Access-Control-Allow-*` requeridas para autorizar la comunicación cruzada.
   * **Mitigación de Slowloris:** Timeout estricto de 3.0 segundos para la lectura de cabeceras HTTP.
   * **Bomba de RAM:** Rechazo inmediato (HTTP 413) si el encabezado `Content-Length` supera los 10 Megabytes.

---

## 📂 Estructura del Repositorio
```text
~/proyectos/nano-rag/
├── .gitignore                 <-- Exclusión de metadatos (__pycache__/) y variables de entorno.
├── Dockerfile                 <-- Contenedor Alpine robustecido con certificados CA nativos.
├── SPEC_CHAT_AGENT.md         <-- Contrato técnico y guardarraíles lógicos.
├── CONTEXTO_SESION.md         <-- Historial narrativo del desarrollo.
├── README.md                  <-- Presentación del proyecto y guía de despliegue.
├── app.py                     <-- Orquestador maestro central asíncrono y ciclo de vida.
├── server.py                  <-- Servidor HTTP nativo con contexto SSL seguro.
├── watcher.py                 <-- Corrutina asíncrona de monitoreo de archivos (Hot-Reload).
├── indexador.py               <-- Extractor utilitario de archivos CSV a memoria RAM.
├── buscador.py                <-- Motor léxico con expansión semántica (Tesauro).
├── test_stress.py             <-- Arnés concurrente para auditoría de carga y seguridad.
├── index.html                 <-- Interfaz de usuario "PodoChat" estilo Google.
└── knowledge/                 
    ├── podologia_faq.csv      <-- Base de conocimientos de preguntas frecuentes clínicas.
    └── clinica_info.csv       <-- Datos de simulación comercial (Horarios y Tarifas).
```

---

## 🛠️ Tecnologías y Herramientas
* **Lenguaje:** Python 3.14.4 Standard (Sin frameworks externos como FastAPI o Flask, cero `pip`).
* **Concurrencia:** `asyncio` nativo, `asyncio.start_server`, `asyncio.Lock`, `asyncio.to_thread`.
* **Criptografía:** `hashlib` (SHA-256) y `ssl` (Contexto criptográfico verificado por `ca-certificates`).
* **Entorno Local:** WSL (Windows Subsystem for Linux), VS Code, Terminal Warp.
* **Contenedorización:** Docker (`python:3.14-alpine`).
* **Nube Productiva:** Render Cloud (Instancia Docker Web Service) coordinada con el Router de Hugging Face (`meta-llama/Llama-3.1-8B-Instruct`).

---

## 🚀 Instrucciones para Ejecutar el Proyecto

### Ejecución Local (Desarrollo)
1. Asegúrate de tener Python 3.11 o superior instalado.
2. Clona el repositorio y navega a la raíz:
   ```bash
   git clone https://github.com
   cd nano-rag
   ```
3. Inicia el orquestador unificado:
   ```bash
   python3 app.py
   ```

### Pruebas de Estrés y Seguridad
Puedes lanzar de forma local el arnés concurrente diseñado para certificar la invulnerabilidad ante ataques informáticos:
```bash
python3 test_stress.py
```

---

## 📂 Contrato de Mapeo Dinámico de Datos (CSV)
El sistema expande su conocimiento de forma automatizada. Soporta cualquier documento guardado en `knowledge/` bajo dos estructuras normalizadas:

* **Esquema Clínico (`podologia_faq.csv`):** Columnas `categoria`, `palabras_clave`, `respuesta_oficial`.
* **Esquema de Simulación Comercial (`clinica_info.csv`):** Columnas `categoria`, `concepto`, `detalle`.

---

## 💬 Ejemplos de Interacción (RAG en Acción)

### Ejemplo de Pregunta Comercial (Payload JSON)
```json
{
  "pregunta": "¿Cuáles son los horarios de atención el sábado?"
}
```

### Ejemplo de Respuesta (HTTP 200 OK)
```json
{
  "respuesta": "**Diagnóstico y tratamiento**\n\nLa clínica ofrece servicios comerciales y operativos estructurados de forma regular. El horario de atención para los días sábados corresponde a las 10:00 a 14:00 horas.\n\n**Acciones directas**\n\n* Agendar con anticipación la cita.\n* Verificar disponibilidad del personal.\n* Acudir en el horario corrido establecido.\n\nNota: Esta es una guía informativa y no reemplaza la consulta con un podólogo profesional."
}
```

---

## ☁️ Evidencia del Deploy en la Nube
* **Enlace Público del Backend API:** `https://onrender.com`
* **Método de Prueba Global:** 
  ```bash
  curl -i -X POST https://onrender.com -H "Content-Type: application/json" -d '{"pregunta": "¿Cuáles son los horarios de atención el sábado?"}'
  ```
