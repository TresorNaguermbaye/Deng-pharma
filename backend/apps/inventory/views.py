from django.db import transaction, models
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from datetime import date, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F, Q,Avg
from apps.medicines.models import Medicine,Category
from apps.inventory.models import StockLot
from apps.sales.models import SaleItem
from .models import StockLot, StockMovement
from .serializers import StockLotSerializer, StockMovementSerializer
from apps.notifications.models import Notification
from apps.accounts.permissions import AuditeurReadOnly
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsAdminOrReadOnly

class StockLotViewSet(viewsets.ModelViewSet):
    """CRUD pour les lots de stock"""
    queryset = StockLot.objects.select_related('medicine').all()
    serializer_class = StockLotSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

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
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

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

# backend/apps/inventory/views.py

class OutOfStockView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Médicaments dont le stock total (non expiré) <= 0
        out_of_stock_ids = (
            StockLot.objects.filter(expiry_date__gte=date.today())
            .values('medicine')
            .annotate(total=Sum('quantity'))
            .filter(total__lte=0)
            .values_list('medicine', flat=True)
        )
        medicines = Medicine.objects.filter(id__in=out_of_stock_ids).select_related('category')

        data = []
        for med in medicines:
            # Stock actuel = 0 (car en rupture)
            current_stock = 0

            # Moyenne des ventes quotidiennes sur les 30 derniers jours
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            avg_sales = SaleItem.objects.filter(
                medicine=med,
                sale__created_at__date__gte=thirty_days_ago
            ).aggregate(avg=Avg('quantity'))['avg'] or 0

            # Règle : stock_max - stock_actuel, mais au moins la moyenne des ventes * 7 jours
            simple_suggestion = max(med.max_stock - current_stock, 0)
            ai_suggestion = max(int(avg_sales * 7), 0)
            recommended = max(simple_suggestion, ai_suggestion)

            # Si aucune donnée de vente, on utilise la règle simple
            if recommended == 0:
                recommended = med.max_stock

            data.append({
                'id': med.id,
                'name': med.commercial_name,
                'category': med.category.name if med.category else '',
                'recommended_order': recommended,
            })

        return Response(data)