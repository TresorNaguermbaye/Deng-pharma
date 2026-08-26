# backend/apps/accounts/models.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
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