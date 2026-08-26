# backend/apps/notifications/tasks.py
from celery import shared_task
from django.db.models import Avg, Sum
from django.utils import timezone
from datetime import timedelta

from apps.medicines.models import Medicine
from apps.notifications.models import Notification
from apps.notifications.utils import send_push_notification   # <-- import ajouté
from apps.accounts.models import User
from apps.inventory.models import StockLot
from apps.sales.models import SaleItem
from ai_client import ai_client

@shared_task
def check_ai_alerts():
    """Analyse les prédictions IA et crée des notifications si nécessaire."""
    medicines = Medicine.objects.all()
    admins = User.objects.filter(role__in=['ADMIN', 'GESTIONNAIRE'], is_active=True)

    for med in medicines:
        try:
            prediction = ai_client.predict_sales(str(med.id), days_ahead=7)
            predictions = prediction.get('predictions', [])
            if not predictions:
                continue

            avg_7d = sum(p['predicted_sales'] for p in predictions) / len(predictions)

            thirty_days_ago = timezone.now() - timedelta(days=30)
            historical_avg = SaleItem.objects.filter(
                medicine=med,
                sale__created_at__gte=thirty_days_ago
            ).aggregate(avg=Avg('quantity'))['avg'] or 0

            # Pic de demande
            if historical_avg and avg_7d > historical_avg * 1.5:
                message = f"Pic de demande prévu pour {med.commercial_name} : {avg_7d:.1f} unités/jour en moyenne (vs {historical_avg:.1f})."
                for admin in admins:
                    Notification.objects.create(user=admin, type='AI_PREDICTION', message=message)
                    send_push_notification(admin, "DENG PHARMA", message)   # <-- push

            # Suggestion de commande
            current_stock = StockLot.objects.filter(
                medicine=med,
                expiry_date__gte=timezone.localdate()
            ).aggregate(total=Sum('quantity'))['total'] or 0
            needed_7d = avg_7d * 7
            if current_stock < needed_7d:
                message = f"Commander maintenant : {med.commercial_name} – stock actuel {current_stock}, besoin estimé {needed_7d:.0f} unités pour 7 jours."
                for admin in admins:
                    Notification.objects.create(user=admin, type='AI_PREDICTION', message=message)
                    send_push_notification(admin, "DENG PHARMA", message)   # <-- push

        except Exception as e:
            print(f"Erreur IA pour {med.commercial_name}: {e}")

@shared_task
def train_model_auto():
    """Déclenche l'entraînement du modèle IA via le client."""
    result = ai_client.train_model()
    return result