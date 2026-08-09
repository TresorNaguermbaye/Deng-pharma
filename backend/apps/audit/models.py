# backend/apps/audit/models.py
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    """Journal d'audit des actions sensibles"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)  # ex: 'CREATE_SALE', 'UPDATE_MEDICINE'
    object_type = models.CharField(max_length=100)  # ex: 'Sale', 'Medicine'
    object_id = models.PositiveIntegerField()
    changes = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"
        ordering = ['-timestamp']