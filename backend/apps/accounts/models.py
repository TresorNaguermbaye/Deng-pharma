# backend/apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

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
    """
    Profil étendu pour chaque utilisateur.
    Stocke la photo, la langue, la devise et les préférences de notification.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    langue = models.CharField(
        max_length=10,
        choices=[('fr', 'Français'), ('en', 'English')],
        default='fr'
    )
    devise = models.CharField(
        max_length=10,
        choices=[('FCFA', 'FCFA'), ('EUR', 'Euro'), ('USD', 'Dollar US')],
        default='FCFA'
    )
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Profil de {self.user.email}"