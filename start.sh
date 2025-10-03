#!/bin/bash

# Script para iniciar tanto el servidor de acciones como el servidor Rasa

# Usar el puerto proporcionado por Railway o 5005 por defecto
RASA_PORT=${PORT:-5005}
ACTIONS_PORT=5055

echo "Iniciando servidor de acciones de Rasa en puerto $ACTIONS_PORT..."
rasa run actions --port $ACTIONS_PORT &

# Esperar un poco para que el servidor de acciones se inicie
sleep 5

echo "Iniciando servidor Rasa en puerto $RASA_PORT..."
rasa run --enable-api --cors "*" --port $RASA_PORT --host 0.0.0.0

# Mantener el script corriendo
wait
