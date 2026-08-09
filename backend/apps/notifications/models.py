# backend/apps/notifications/models.py
from django.db import models
from django.conf import settings

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