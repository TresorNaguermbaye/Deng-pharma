from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import StockMovement, StockLot
from apps.notifications.models import Notification
from apps.accounts.models import User
from django.db.models import Sum
from datetime import date

print("✅ Signaux inventory chargés")

@receiver(post_save, sender=StockMovement)
def check_stock_levels(sender, instance, created, **kwargs):
    print(f"🔔 SIGNAL REÇU - created={created}, movement_id={instance.id}")
    # Le reste du code...
    
    medicine = instance.medicine
    
    # Calculer le stock total
    total_stock = StockLot.objects.filter(
        medicine=medicine,
        expiry_date__gte=date.today()
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Récupérer les utilisateurs à notifier
    recipients = User.objects.filter(role__in=['ADMIN', 'GESTIONNAIRE', 'PHARMACIEN'], is_active=True)
    
    # Rupture
    if total_stock == 0:
        message = f"🚨 RUPTURE : {medicine.commercial_name} est en rupture de stock !"
        for user in recipients:
            Notification.objects.create(user=user, type='STOCK_OUT', message=message)
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
    
    # Stock faible
    elif total_stock <= medicine.min_stock:
        message = f"⚠️ STOCK FAIBLE : {medicine.commercial_name} - {total_stock} restants (min: {medicine.min_stock})"
        for user in recipients:
            Notification.objects.create(user=user, type='STOCK_LOW', message=message)
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
