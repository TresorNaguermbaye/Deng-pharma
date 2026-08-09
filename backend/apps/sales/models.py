# backend/apps/sales/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from apps.medicines.models import Medicine
from apps.inventory.models import StockLot

class Sale(models.Model):
    """Vente en pharmacie"""
    PAYMENT_METHODS = (
        ('CASH', 'Espèces'),
        ('CARD', 'Carte bancaire'),
        ('MOBILE', 'Mobile Money'),
        ('OTHER', 'Autre'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Pharmacien")
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='CASH')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Vente #{self.id} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class SaleItem(models.Model):
    """Ligne de vente"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de vente"
        verbose_name_plural = "Lignes de vente"

    def __str__(self):
        return f"{self.medicine.commercial_name} x{self.quantity}"