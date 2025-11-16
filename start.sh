#!/bin/bash
# Universal start script for Railway
# Checks SERVICE_TYPE environment variable to decide what to run

if [ "$SERVICE_TYPE" = "cron" ]; then
    echo "Starting cron service..."
    exec python run_cron_reminders.py
elif [ "$SERVICE_TYPE" = "web" ]; then
    echo "Starting web service..."
    exec gunicorn 'backend.app:create_app()' --bind 0.0.0.0:$PORT --workers=1 --timeout=300 --worker-class=sync --preload --access-logfile=- --error-logfile=- --log-level=info
else
    echo "ERROR: SERVICE_TYPE not set or invalid. Set to 'web' or 'cron'"
    exit 1
fi

