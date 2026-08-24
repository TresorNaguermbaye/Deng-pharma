# backend/apps/accounts/models.py
from datetime import timezone
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta
from django.conf import settings


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour DENG PHARMA.
    Ajoute un champ 'role' pour la gestion des accès (RBAC).
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        GESTIONNAIRE = 'GESTIONNAIRE', 'Gestionnaire'
        PHARMACIEN = 'PHARMACIEN', 'Pharmacien'
        AUDITEUR = 'AUDITEUR', 'Auditeur'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PHARMACIEN,
        verbose_name="Rôle"
    )

    has_completed_onboarding = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    langue = models.CharField(max_length=5, choices=[('fr', 'Français'), ('en', 'English')], default='fr')
    devise = models.CharField(max_length=5, choices=[('FCFA', 'FCFA'), ('EUR', 'EUR'), ('USD', 'USD')], default='FCFA')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Profil de {self.user.username}"
class PasswordResetToken(models.Model):
    """Token de réinitialisation de mot de passe avec expiration."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"Reset token pour {self.user.email}"
