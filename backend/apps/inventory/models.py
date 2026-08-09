# backend/apps/inventory/models.py
from datetime import date
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from apps.medicines.models import Medicine

class StockLot(models.Model):
    """Lot de médicaments avec date d'expiration"""
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='stock_lots')
    batch_number = models.CharField(max_length=100, verbose_name="Numéro de lot")
    quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(verbose_name="Date d'expiration")
    received_date = models.DateField(auto_now_add=True)
    purchase_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "Lot de stock"
        verbose_name_plural = "Lots de stock"
        ordering = ['expiry_date']  # FEFO : le plus proche expiration en premier
        indexes = [
            models.Index(fields=['expiry_date']),
            models.Index(fields=['batch_number']),
        ]

    def __str__(self):
        return f"{self.medicine.commercial_name} - Lot {self.batch_number}"

class StockMovement(models.Model):
    """Mouvement de stock (entrée ou sortie)"""
    MOVEMENT_TYPES = (
        ('IN', 'Entrée'),
        ('OUT', 'Sortie'),
    )
    REASONS = (
        ('PURCHASE', 'Achat'),
        ('DONATION', 'Don'),
        ('RETURN', 'Retour fournisseur'),
        ('SALE', 'Vente'),
        ('LOSS', 'Perte'),
        ('EXPIRATION', 'Expiration'),
        ('ADJUSTMENT', 'Ajustement inventaire'),
    )

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True, blank=True)
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    reason = models.CharField(max_length=20, choices=REASONS)
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=100, blank=True, help_text="N° commande, vente, etc.")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Appliquer FEFO automatiquement pour les sorties si le lot n'est pas spécifié
        if self.movement_type == 'OUT' and not self.lot:
            # Sélectionner le lot disponible avec la date d'expiration la plus proche
            available_lot = StockLot.objects.filter(
                medicine=self.medicine,
                quantity__gt=0,
                expiry_date__gte=date.today()
            ).order_by('expiry_date').first()
            if available_lot:
                self.lot = available_lot
            else:
                raise ValueError("Aucun lot disponible pour ce médicament")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.medicine.commercial_name} ({self.quantity})"