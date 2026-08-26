# backend/apps/notifications/models.py
from django.db import models
from django.conf import settings






class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push subscription for {self.user.username}"
    
class Notification(models.Model):
    """Notification pour les utilisateurs"""
    TYPES = (
        ('STOCK_LOW', 'Stock faible'),
        ('STOCK_OUT', 'Rupture de stock'),
        ('EXPIRY_SOON', 'Expiration proche'),
        ('OVERSTOCK', 'Surstock'),
        ('AI_PREDICTION', 'Nouvelle prédiction IA'),
        ('TRAINING_COMPLETE', 'Entraînement IA terminé'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification pour {self.user.email}: {self.type}"