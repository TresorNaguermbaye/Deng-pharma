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

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"