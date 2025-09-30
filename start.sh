#!/bin/bash

# Script para iniciar tanto el servidor de acciones como el servidor Rasa

echo "Iniciando servidor de acciones de Rasa..."
rasa run actions --port 5055 &

# Esperar un poco para que el servidor de acciones se inicie
sleep 5

echo "Iniciando servidor Rasa..."
rasa run --enable-api --cors "*" --port 5005 -i 0.0.0.0

# Mantener el script corriendo
wait
