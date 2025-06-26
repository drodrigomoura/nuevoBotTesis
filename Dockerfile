# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Configurar los repositorios de apt y manejar mejor los errores de red
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80-retries && \
    echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bullseye-security main" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bullseye-updates main" >> /etc/apt/sources.list

# Instalar dependencias del sistema necesarias con reintentos
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Rasa y otras dependencias de Python con versiones específicas
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    rasa==3.1 \
    python-dotenv==1.0.0 \
    supabase==1.0.3 \
    httpx==0.23.3 \
    typing-extensions==3.10.0.2

# Copiar los archivos del proyecto
COPY . .

# Exponer el puerto que usa Rasa
EXPOSE 5005

# Entrenar el modelo al construir la imagen
RUN rasa train

# Comando para iniciar el servidor Rasa
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005", "--host", "0.0.0.0"]

FROM rasa/rasa:3.6.20-full

WORKDIR /app

COPY . .

RUN rasa train

# El comando se especificará en docker-compose 