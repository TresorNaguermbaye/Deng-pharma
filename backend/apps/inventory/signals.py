from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import StockMovement, StockLot
from apps.notifications.models import Notification
from apps.notifications.utils import send_push_notification   # <-- import ajouté
from apps.accounts.models import User
from django.db.models import Sum
from datetime import date

print("✅ Signaux inventory chargés")

@receiver(post_save, sender=StockMovement)
def handle_stock_movement(sender, instance, created, **kwargs):
    if created:
        # 1. Mettre à jour la quantité du lot
        lot = instance.lot
        if instance.movement_type == 'IN':
            lot.quantity += instance.quantity
        elif instance.movement_type == 'OUT':
            lot.quantity -= instance.quantity
        lot.save(update_fields=['quantity'])

        # 2. Vérifier les niveaux de stock et notifier
        medicine = instance.medicine
        total_stock = StockLot.objects.filter(
            medicine=medicine,
            expiry_date__gte=date.today()
        ).aggregate(total=Sum('quantity'))['total'] or 0

        recipients = User.objects.filter(role__in=['ADMIN', 'GESTIONNAIRE', 'PHARMACIEN'], is_active=True)

        if total_stock == 0:
            message = f"🚨 RUPTURE : {medicine.commercial_name} est en rupture de stock !"
            for user in recipients:
                Notification.objects.create(user=user, type='STOCK_OUT', message=message)
                send_push_notification(user, "DENG PHARMA", message)   # <-- notification push
                try:
                    send_mail(
                        'DENG PHARMA - Alerte Rupture',
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )
                except:
                    pass

        elif total_stock <= medicine.min_stock:
            message = f"⚠️ STOCK FAIBLE : {medicine.commercial_name} - {total_stock} restants (min: {medicine.min_stock})"
            for user in recipients:
                Notification.objects.create(user=user, type='STOCK_LOW', message=message)
                send_push_notification(user, "DENG PHARMA", message)   # <-- notification push
                try:
                    send_mail(
                        'DENG PHARMA - Alerte Stock Faible',
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )
                except:
                    pass