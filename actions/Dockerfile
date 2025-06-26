FROM rasa/rasa-sdk:3.6.2

WORKDIR /app

# Copiar requirements.txt para las dependencias de las acciones
COPY requirements.txt .

# Instalar dependencias
RUN pip install -r requirements.txt

# Copiar el código de las acciones
COPY . .

# El comando se especificará en docker-compose 