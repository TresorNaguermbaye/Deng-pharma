# apps/settings/models.py
from django.db import models

class SiteSettings(models.Model):
    """Paramètres du site (logo, nom, etc.)"""
    
    logo = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        help_text="Logo de la pharmacie (PNG, JPG)"
    )
    
    site_name = models.CharField(
        max_length=100,
        default='DENG PHARMA',
        help_text="Nom du site"
    )
    
    slogan = models.CharField(
        max_length=200,
        default='Pharmacie intelligente',
        blank=True,
        help_text="Slogan du site"
    )
    
    phone = models.CharField(
        max_length=20,
        default='+235 XX XX XX XX',
        blank=True,
        help_text="Numéro de téléphone"
    )
    
    address = models.CharField(
        max_length=255,
        default="N'Djaména, Tchad",
        blank=True,
        help_text="Adresse de la pharmacie"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paramètre du site"
        verbose_name_plural = "Paramètres du site"
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """Récupère les paramètres (crée les défauts si inexistants)"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'site_name': 'DENG PHARMA',
                'slogan': 'Pharmacie intelligente',
                'phone': '+235 XX XX XX XX',
                'address': "N'Djaména, Tchad"
            }
        )
        return settings