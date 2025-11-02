# Imagen base moderna compatible con Rasa 3.6
FROM python:3.10-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV RASA_TELEMETRY_ENABLED=false

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    git \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Crear usuario no root
RUN useradd -m -u 1001 rasa && \
    chown -R rasa:rasa /app
USER rasa

# Exponer puerto estándar de Rasa
EXPOSE 5005

# Comando por defecto
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005"]