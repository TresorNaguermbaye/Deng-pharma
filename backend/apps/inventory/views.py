from django.db import transaction, models
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from datetime import date

from .models import StockLot, StockMovement
from .serializers import StockLotSerializer, StockMovementSerializer
from apps.notifications.models import Notification
from apps.accounts.permissions import AuditeurReadOnly

class StockLotViewSet(viewsets.ModelViewSet):
    """CRUD pour les lots de stock"""
    queryset = StockLot.objects.select_related('medicine').all()
    serializer_class = StockLotSerializer
    permission_classes = [permissions.IsAuthenticated, AuditeurReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        medicine_id = self.request.query_params.get('medicine')
        if medicine_id:
            qs = qs.filter(medicine_id=medicine_id)
        expired = self.request.query_params.get('expired')
        if expired == 'true':
            qs = qs.filter(expiry_date__lt=date.today())
        elif expired == 'false':
            qs = qs.filter(expiry_date__gte=date.today())
        return qs

class StockMovementViewSet(viewsets.ModelViewSet):
    """CRUD pour les mouvements de stock avec logique FEFO et mise à jour des quantités"""
    queryset = StockMovement.objects.select_related('medicine', 'lot', 'performed_by').all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated, AuditeurReadOnly]

    def perform_create(self, serializer):
        with transaction.atomic():
            movement = serializer.save(performed_by=self.request.user)
            if movement.lot:
                lot = movement.lot
                if movement.movement_type == 'IN':
                    lot.quantity += movement.quantity
                elif movement.movement_type == 'OUT':
                    lot.quantity -= movement.quantity
                lot.save(update_fields=['quantity'])

            self.check_stock_alerts(movement)

    def check_stock_alerts(self, movement):
        medicine = movement.medicine
        total_stock = StockLot.objects.filter(
            medicine=medicine,
            expiry_date__gte=date.today()
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        if total_stock == 0:
            self.create_notification(medicine, 'STOCK_OUT', f"Rupture de stock pour {medicine.commercial_name}")
        elif total_stock <= medicine.min_stock:
            self.create_notification(medicine, 'STOCK_LOW', f"Stock faible pour {medicine.commercial_name} : {total_stock} restants (seuil : {medicine.min_stock})")
        if total_stock >= medicine.max_stock:
            self.create_notification(medicine, 'OVERSTOCK', f"Surstock pour {medicine.commercial_name} : {total_stock} (max : {medicine.max_stock})")

    def create_notification(self, medicine, notif_type, message):
        from apps.accounts.models import User
        admins = User.objects.filter(role__in=['ADMIN', 'GESTIONNAIRE'])
        for admin in admins:
            Notification.objects.create(
                user=admin,
                type=notif_type,
                message=message
            )