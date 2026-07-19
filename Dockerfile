# 1. Imagen base oficial de Python 3.14 sobre Alpine Linux
FROM python:3.14-alpine

# 2. Configurar variables de entorno óptimas para Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Crear un usuario de sistema no-privilegiado por seguridad
RUN adduser -D appuser && chown -R appuser:appuser /app

# 5. Copiar la totalidad del código y datos del repositorio al contenedor
COPY --chown=appuser:appuser . .

# 6. Cambiar al contexto del usuario seguro
USER appuser

# 7. Exponer el puerto estandarizado para Hugging Face Spaces
EXPOSE 7860

# 8. Comando de ejecución nativo para levantar el orquestador central
CMD ["python", "app.py"]
