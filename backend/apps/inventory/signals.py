# apps/inventory/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import StockMovement, StockLot
from apps.notifications.models import Notification
from apps.notifications.utils import send_push_notification
from apps.accounts.models import User
from django.db.models import Sum
from datetime import date
import logging

logger = logging.getLogger(__name__)

print("✅ Signaux inventory chargés")

# Cache pour éviter les doublons (au cas où le signal serait chargé plusieurs fois)
_processed_movements = set()

@receiver(post_save, sender=StockMovement, dispatch_uid='stock_movement_handler_unique')
def handle_stock_movement(sender, instance, created, **kwargs):
    """
    Gère les mouvements de stock avec dispatch_uid pour éviter les doublons.
    La décrémentation du stock est faite UNIQUEMENT ici.
    """
    # ✅ ÉVITER LES DOUBLONS
    if not created:
        logger.info(f"⏭️ Mouvement {instance.id} modifié (pas de création) - ignoré")
        return
    
    if instance.pk in _processed_movements:
        logger.warning(f"⚠️ Mouvement {instance.pk} déjà traité - ignoré")
        return
    
    if hasattr(instance, '_processed'):
        logger.warning(f"⚠️ Mouvement {instance.id} déjà marqué comme traité - ignoré")
        return
    
    # Marquer comme traité
    _processed_movements.add(instance.pk)
    instance._processed = True
    
    logger.info(f"🔔 Traitement du mouvement {instance.id} - {instance.movement_type} de {instance.quantity} unités")
    
    # 1. METTRE À JOUR LA QUANTITÉ DU LOT
    try:
        lot = instance.lot
        
        if not lot:
            logger.error(f"❌ Lot non trouvé pour le mouvement {instance.id}")
            return
        
        # Décrémenter ou incrémenter le stock
        if instance.movement_type == 'IN':
            lot.quantity += instance.quantity
            logger.info(f"📥 Entrée: +{instance.quantity} unités → {lot.quantity}")
        elif instance.movement_type == 'OUT':
            # Vérifier le stock avant de décrémenter
            if lot.quantity < instance.quantity:
                logger.error(f"❌ Stock insuffisant: {lot.quantity} < {instance.quantity}")
                raise ValueError(f"Stock insuffisant pour le lot {lot.id}")
            lot.quantity -= instance.quantity
            logger.info(f"📤 Sortie: -{instance.quantity} unités → {lot.quantity}")
        else:
            logger.warning(f"⚠️ Type de mouvement inconnu: {instance.movement_type}")
            return
        
        lot.save(update_fields=['quantity'])
        logger.info(f"✅ Lot {lot.id} mis à jour: {lot.medicine.commercial_name} - {lot.quantity} unités")
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour stock: {e}")
        return

    # 2. VÉRIFIER LES NIVEAUX DE STOCK ET NOTIFIER (uniquement pour les sorties)
    if instance.movement_type == 'OUT':
        medicine = instance.medicine
        total_stock = StockLot.objects.filter(
            medicine=medicine,
            expiry_date__gte=date.today()
        ).aggregate(total=Sum('quantity'))['total'] or 0

        logger.info(f"📊 Stock total pour {medicine.commercial_name}: {total_stock}")

        recipients = User.objects.filter(
            role__in=['ADMIN', 'GESTIONNAIRE', 'PHARMACIEN'],
            is_active=True
        )

        # RUPTURE DE STOCK
        if total_stock == 0:
            message = f"🚨 RUPTURE : {medicine.commercial_name} est en rupture de stock !"
            logger.warning(f"🚨 {message}")
            
            for user in recipients:
                # Notification en base
                Notification.objects.create(
                    user=user,
                    type='STOCK_OUT',
                    message=message
                )
                # Push notification
                send_push_notification(user, "DENG PHARMA", message)
                # Email
                try:
                    send_mail(
                        'DENG PHARMA - Alerte Rupture',
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )
                except Exception as e:
                    logger.error(f"❌ Erreur envoi email: {e}")

        # STOCK FAIBLE
        elif total_stock <= medicine.min_stock:
            message = f"⚠️ STOCK FAIBLE : {medicine.commercial_name} - {total_stock} restants (min: {medicine.min_stock})"
            logger.warning(f"⚠️ {message}")
            
            for user in recipients:
                # Notification en base
                Notification.objects.create(
                    user=user,
                    type='STOCK_LOW',
                    message=message
                )
                # Push notification
                send_push_notification(user, "DENG PHARMA", message)
                # Email
                try:
                    send_mail(
                        'DENG PHARMA - Alerte Stock Faible',
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )
                except Exception as e:
                    logger.error(f"❌ Erreur envoi email: {e}")

    logger.info(f"✅ Mouvement {instance.id} traité avec succès")