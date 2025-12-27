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
    exec gunicorn 'backend.app:create_app()' --bind 0.0.0.0:$PORT --workers=1 --timeout=300 --worker-class=sync --preload --access-logfile=- --error-logfile=- --log-level=info
else
    echo "ERROR: SERVICE_TYPE not set or invalid. Set to 'web' or 'cron'"
    exit 1
fi

