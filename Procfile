web: cd api && python manage.py migrate && gunicorn paperwaves.wsgi:application --bind 0.0.0.0:$PORT
worker: cd api && celery -A paperwaves worker --loglevel=info
