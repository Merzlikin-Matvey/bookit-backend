#!/bin/sh

echo "ENV_TYPE: $ENV_TYPE"

gunicorn telegram.__main__:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${TELEGRAM_SERVER_PORT}" \
  --access-logfile - &

GUNICORN_PID=$!

sleep 25

curl -X POST http://localhost:8010/start_bot

wait $GUNICORN_PID
