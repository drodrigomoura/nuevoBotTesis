# Usar imagen base de Python limpia
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear requirements.txt temporal con versiones específicas compatibles
RUN echo "rasa==3.6.20" > requirements.txt && \
    echo "rasa-sdk==3.6.2" >> requirements.txt && \
    echo "websockets==10.4" >> requirements.txt && \
    echo "sanic==21.12.2" >> requirements.txt && \
    echo "spacy>=3.4.0,<3.5.0" >> requirements.txt && \
    echo "python-dotenv==1.0.0" >> requirements.txt && \
    echo "supabase==1.0.3" >> requirements.txt && \
    echo "httpx==0.23.3" >> requirements.txt

# Instalar todas las dependencias de una vez
RUN pip install --no-cache-dir -r requirements.txt

# Instalar modelo de spaCy para español
RUN python -m spacy download es_core_news_sm

# Eliminar requirements.txt temporal
RUN rm requirements.txt

# Copiar archivos de configuración
COPY config.yml domain.yml credentials.yml endpoints.yml ./
COPY data/ ./data/
COPY actions/ ./actions/

# Copiar modelo existente
COPY models/ ./models/

# Cambiar a root para permisos de archivos
USER root
COPY start.sh .
RUN chmod +x start.sh
RUN chown 1001:1001 start.sh

# Volver al usuario rasa
USER 1001

# Exponer puertos para Rasa y acciones
EXPOSE 5005 5055

# Comando por defecto - ejecutar script de inicio
CMD ["./start.sh"]