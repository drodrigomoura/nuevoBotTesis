# Usar la imagen oficial de Rasa con la versión correcta
FROM rasa/rasa:3.6.20-full

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar dependencias adicionales si las hay
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de configuración
COPY config.yml domain.yml credentials.yml endpoints.yml ./
COPY data/ ./data/

# Crear directorio de modelos
RUN mkdir -p ./models/

# Si no hay modelo, entrenar uno nuevo
RUN if [ -z "$(ls -A models 2>/dev/null)" ]; then rasa train; fi

# Exponer el puerto que usa Rasa
EXPOSE 5005

# Comando por defecto
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005", "--host", "0.0.0.0"]