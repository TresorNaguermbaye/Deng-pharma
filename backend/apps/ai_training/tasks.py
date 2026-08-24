from celery import shared_task
from ai_client import ai_client

@shared_task
def train_model_auto():
    """Tâche Celery qui déclenche l'entraînement du modèle IA."""
    result = ai_client.train_model()
    return result