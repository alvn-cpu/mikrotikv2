web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn wifi_billing_system.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: celery -A wifi_billing_system worker --loglevel=info
beat: celery -A wifi_billing_system beat --loglevel=info