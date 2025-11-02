FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV RASA_TELEMETRY_ENABLED=false

# Instalar dependencias del sistema (cambian muy raramente)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    git \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip (capa separada)
RUN pip install --upgrade pip

# Copiar e instalar requirements (solo se reinstala si cambia requirements.txt)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar archivos de configuración de Rasa (cambian ocasionalmente)
COPY config.yml domain.yml endpoints.yml credentials.yml ./
COPY data/ ./data/

# Copiar actions (si cambias código, solo se recompila desde acá)
COPY actions/ ./actions/

# Crear usuario no root
RUN useradd -m -u 1001 rasa && \
    chown -R rasa:rasa /app
USER rasa

EXPOSE 5005

CMD ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005"]