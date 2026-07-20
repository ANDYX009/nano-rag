# 🩻 Nano-RAG: Agente Podológico Asíncrono de Bajo Nivel

## 🎯 Descripción General
Este proyecto consiste en un **Agente de Inteligencia Artificial (RAG)** enfocado en la atención y orientación médica podológica. A diferencia de las arquitecturas tradicionales basadas en frameworks pesados, esta solución fue construida desde los cimientos del sistema utilizando **Python 3.14 Standard**, sockets TCP de bajo nivel y un parser manual de bytes optimizado para alta concurrencia y seguridad perimetral.

---

## 🏗️ Arquitectura de la Solución
La aplicación opera mediante un modelo de orquestación central asíncrona (`asyncio.gather`) dividida en dos componentes críticos que comparten memoria en RAM:

1. **File Watcher Seguro (`watcher.py`):** Monitorea en segundo plano el archivo `knowledge/podologia_faq.csv`. Mediante hashes criptográficos (SHA-256) detecta mutaciones físicas en tiempo real y, utilizando un candado mutuo (`asyncio.Lock`), inyecta los datos de forma exclusiva en la memoria compartida de la aplicación.
2. **Servidor HTTP Nativo (`server.py`):** Levanta un socket TCP en la interfaz `0.0.0.0` capaz de recibir peticiones concurrentes cruzando la WAN. Cuenta con blindaje perimetral activo:
   * **Mitigación de Slowloris:** Timeout estricto de 3.0 segundos para la lectura de cabeceras.
   * **Bomba de RAM:** Rechazo inmediato (HTTP 413) si el encabezado `Content-Length` supera los 10 Megabytes.

---

## 🛠️ Tecnologías y Herramientas
* **Lenguaje:** Python 3.14.4 Standard (Sin frameworks externos como FastAPI o Flask).
* **Concurrencia:** `asyncio` nativo, `asyncio.start_server`, `asyncio.Lock`, `asyncio.to_thread`.
* **Criptografía:** `hashlib` (SHA-256).
* **Entorno Local:** WSL (Windows Subsystem for Linux), VS Code, Terminal Warp.
* **Contenedorización:** Docker (`python:3.14-alpine`).
* **Nube Productiva:** Render Cloud (Instancia Docker Web Service).

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

## 💬 Ejemplos de Interacción (RAG en Acción)

### Ejemplo de Pregunta (Payload JSON)
```json
{
  "pregunta": "Tengo onicocriptosis dolorosa"
}
```

### Ejemplo de Respuesta (HTTP 200 OK)
```json
{
  "respuesta": "Asistente Médico Podológico: Con base en el historial clínico indexado, su consulta sobre 'Tengo onicocriptosis dolorosa' sugiere una atención prioritaria. Por favor, mantenga la higiene de la zona, evite la manipulación casera y acuda a valoración.\n\n*Nota: Esta es una guía informativa y no reemplaza la consulta con un podólogo profesional.*"
}
```

---

## ☁️ Evidencia del Deploy en la Nube
* **Enlace Público del Backend API:** `https://onrender.com`
* **Método de Prueba Global:** 
  ```bash
  curl -i -X POST https://onrender.com -H "Content-Type: application/json" -d '{"pregunta": "Tengo onicocriptosis dolorosa"}'
  ```
