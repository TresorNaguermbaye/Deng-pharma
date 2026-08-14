from django.db import models
from apps.medicines.models import Medicine, Supplier
from apps.accounts.models import User

class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('RECEIVED', 'Reçue'),
        ('CANCELLED', 'Annulée'),
    )

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_ordered = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Commande fournisseur"
        verbose_name_plural = "Commandes fournisseurs"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.id} - {self.medicine.commercial_name}"