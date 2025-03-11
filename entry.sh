#!/bin/sh

echo "ENV_TYPE: $ENV_TYPE"

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 2
done

alembic upgrade head

exec gunicorn server.__main__:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT}" \
  --access-logfile -
