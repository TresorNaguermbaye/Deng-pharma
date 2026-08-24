from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from django.db.models import Q, Sum, Avg

from apps.medicines.models import Medicine
from apps.sales.models import SaleItem
from .models import StockLot, StockMovement
from .serializers import StockLotSerializer, StockMovementSerializer
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
    """CRUD pour les mouvements de stock. La mise à jour du lot et les alertes sont gérées par le signal post_save."""
    queryset = StockMovement.objects.select_related('medicine', 'lot', 'performed_by').all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        # Le signal post_save de StockMovement mettra à jour la quantité du lot
        # et déclenchera les notifications de stock.
        with transaction.atomic():
            serializer.save(performed_by=self.request.user)

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
            current_stock = 0

            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            avg_sales = SaleItem.objects.filter(
                medicine=med,
                sale__created_at__date__gte=thirty_days_ago
            ).aggregate(avg=Avg('quantity'))['avg'] or 0

            simple_suggestion = max(med.max_stock - current_stock, 0)
            ai_suggestion = max(int(avg_sales * 7), 0)
            recommended = max(simple_suggestion, ai_suggestion)

            if recommended == 0:
                recommended = med.max_stock

            data.append({
                'id': med.id,
                'name': med.commercial_name,
                'category': med.category.name if med.category else '',
                'recommended_order': recommended,
            })

        return Response(data)

class InventorySummaryView(APIView):
    """Résumé des stocks pour la page Stock."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        medicines = Medicine.objects.annotate(
            remaining_stock=Sum(
                'stock_lots__quantity',
                filter=Q(stock_lots__expiry_date__gte=today)
            )
        ).values(
            'id', 'commercial_name', 'min_stock', 'max_stock', 'remaining_stock'
        )

        data = []
        for med in medicines:
            remaining = med['remaining_stock'] or 0
            if remaining <= 0:
                status = 'OUT'
            elif remaining < med['min_stock']:
                status = 'LOW'
            elif remaining > med['max_stock']:
                status = 'OVER'
            else:
                status = 'OK'
            data.append({
                'id': med['id'],
                'commercial_name': med['commercial_name'],
                'min_stock': med['min_stock'],
                'max_stock': med['max_stock'],
                'remaining_stock': remaining,
                'status': status,
            })
        return Response(data)