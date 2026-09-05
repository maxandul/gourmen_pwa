#!/bin/bash
# Universal start script for Railway
# Checks SERVICE_TYPE environment variable to decide what to run

if [ "$SERVICE_TYPE" = "cron" ]; then
    echo "Starting cron service..."
    if [ "${TEST_REMINDER_NOW,,}" = "true" ] || [ "${TEST_REMINDER_NOW,,}" = "1" ]; then
        echo "TEST_REMINDER_NOW detected - running test reminder..."
        exec python run_cron_reminders.py --test-reminder
    else
        exec python run_cron_reminders.py
    fi
elif [ "$SERVICE_TYPE" = "web" ]; then
    echo "Starting web service..."
    # Nebenlaeufigkeit: gthread mit 8 Threads statt eines einzelnen sync-Workers.
    # Mit worker-class=sync bediente die App genau EINEN Request gleichzeitig -
    # bei rund 50 Assets pro Seitenaufruf wurden die Stylesheets damit hinter
    # allem anderen serialisiert.
    #
    # Bewusst weiterhin --workers=1: Flask-Limiter laeuft ohne REDIS_URL mit
    # In-Memory-Storage, den sich mehrere Prozesse nicht teilen koennten - die
    # Login-Rate-Limits waeren dann pro Worker statt global. Threads teilen den
    # Speicher und lassen die Limits intakt. Sobald REDIS_URL gesetzt ist,
    # koennen zusaetzlich Worker hochgezogen werden.
    exec gunicorn 'backend.app:create_app()' --bind 0.0.0.0:$PORT --workers=1 --threads=8 --timeout=300 --worker-class=gthread --preload --access-logfile=- --error-logfile=- --log-level=info
else
    echo "ERROR: SERVICE_TYPE not set or invalid. Set to 'web' or 'cron'"
    exit 1
fi

