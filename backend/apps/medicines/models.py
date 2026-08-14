# backend/apps/medicines/models.py
import uuid
from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    """Catégorie de médicaments (ex: Antibiotiques, Antalgiques...)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name

class Medicine(models.Model):
    """Médicament avec informations réglementaires et commerciales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commercial_name = models.CharField(max_length=200, verbose_name="Nom commercial")
    dci = models.CharField(max_length=200, verbose_name="Dénomination Commune Internationale")
    barcode = models.CharField(max_length=50, unique=True, verbose_name="Code-barres")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    image = models.ImageField(upload_to='medicines/', null=True, blank=True)
    description = models.TextField(blank=True)
    manufacturer = models.CharField(max_length=200, verbose_name="Fabricant")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=100, blank=True, verbose_name="Emplacement dans la pharmacie")
    min_stock = models.PositiveIntegerField(default=10, verbose_name="Stock minimum")
    max_stock = models.PositiveIntegerField(default=100, verbose_name="Stock maximum")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['commercial_name']
        verbose_name = "Médicament"
        verbose_name_plural = "Médicaments"
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['dci']),
        ]

    def __str__(self):
        return f"{self.commercial_name} ({self.dci})"
    
class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom du fournisseur")
    contact_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"

    def __str__(self):
        return self.name