#! /usr/bin/env sh
set -e

export APP_MODULE=app.main:app
export GUNICORN_CONF=app/gunicorn_conf.py

# Start Gunicorn
exec gunicorn -k uvicorn.workers.UvicornWorker --log-level=DEBUG --timeout 1800 -c "$GUNICORN_CONF" "$APP_MODULE"
