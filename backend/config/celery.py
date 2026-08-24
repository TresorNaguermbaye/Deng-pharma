# backend/config/celery.py
import os
from celery import Celery
from celery.schedules import crontab

# Définir le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('deng_pharma')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Planification des tâches périodiques
app.conf.beat_schedule = {
    'train-model-every-sunday-3am': {
        'task': 'apps.notifications.tasks.train_model_auto',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # dimanche à 3h
    },
    'check-ai-alerts-every-6-hours': {
        'task': 'apps.notifications.tasks.check_ai_alerts',
        'schedule': crontab(minute=0, hour='*/6'),  # toutes les 6 heures
    },
}