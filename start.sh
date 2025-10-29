#!/usr/bin/env bash
set -euo pipefail

# Puertos (Railway / local)
RASA_PORT="${PORT:-5005}"
ACTIONS_PORT="${ACTIONS_PORT:-5055}"
CORS_VAL="${CORS:-*}"

echo "Configuración de puertos:"
echo "  RASA_PORT: ${RASA_PORT}"
echo "  ACTIONS_PORT: ${ACTIONS_PORT}"

# Apagado prolijo
trap "echo '→ Apagando...'; kill 0" SIGTERM SIGINT

echo "Iniciando servidor de acciones de Rasa en puerto ${ACTIONS_PORT} ..."
rasa run actions --port "${ACTIONS_PORT}" --debug &

# Espera corta
sleep 3

# Buscar el modelo más reciente en /app/models/
MODEL_PATH=$(ls -t /app/models/*.tar.gz 2>/dev/null | head -n 1)
if [ -z "${MODEL_PATH}" ]; then
  echo "ADVERTENCIA: No se encontró ningún modelo en /app/models/"
  echo "Iniciando Rasa sin modelo específico..."
  RASA_ARGS=( --enable-api --cors "${CORS_VAL}" -i 0.0.0.0 -p "${RASA_PORT}" --debug )
else
  echo "Usando modelo: ${MODEL_PATH}"
  RASA_ARGS=( --enable-api --cors "${CORS_VAL}" -i 0.0.0.0 -p "${RASA_PORT}" --debug --model "${MODEL_PATH}" )
fi

echo "Iniciando servidor Rasa en 0.0.0.0:${RASA_PORT} ..."
rasa run "${RASA_ARGS[@]}"

wait -n