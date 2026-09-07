# apps/inventory/views.py
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from django.db.models import Q, Sum, Avg, F
from django.core.exceptions import ValidationError

from apps.medicines.models import Medicine
from apps.sales.models import SaleItem
from .models import StockLot, StockMovement
from .serializers import StockLotSerializer, StockMovementSerializer
from apps.accounts.permissions import IsAdminOrReadOnly
import logging

logger = logging.getLogger(__name__)


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
    """
    CRUD pour les mouvements de stock.
    La mise à jour du lot et les alertes sont gérées par le signal post_save.
    """
    queryset = StockMovement.objects.select_related('medicine', 'lot', 'performed_by').all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        """
        Création d'un mouvement de stock avec validation
        """
        with transaction.atomic():
            movement_type = self.request.data.get('movement_type', 'OUT')
            quantity = int(self.request.data.get('quantity', 0))
            medicine_id = self.request.data.get('medicine')
            lot_id = self.request.data.get('lot')

            # 1. VÉRIFIER LE STOCK POUR LES SORTIES
            if movement_type == 'OUT':
                # Récupérer le lot
                try:
                    lot = StockLot.objects.select_for_update().get(id=lot_id)
                except StockLot.DoesNotExist:
                    raise ValidationError(f"Lot {lot_id} non trouvé")

                # Vérifier la quantité disponible
                if lot.quantity < quantity:
                    raise ValidationError(
                        f"Stock insuffisant. Disponible: {lot.quantity}, Demandé: {quantity}"
                    )

                # Vérifier la péremption
                if lot.expiry_date < date.today():
                    raise ValidationError(
                        f"Lot expiré le {lot.expiry_date}. Impossible de sortir ce produit."
                    )

                logger.info(f"✅ Stock OK pour {lot.medicine.commercial_name}: {lot.quantity} → {lot.quantity - quantity}")

            # 2. ÉVITER LES DOUBLONS (vérifier si un mouvement identique existe déjà)
            # (Optionnel) Vérifier si un mouvement similaire a été créé récemment
            recent_movement = StockMovement.objects.filter(
                medicine_id=medicine_id,
                lot_id=lot_id,
                quantity=quantity,
                movement_type=movement_type,
                created_at__gte=timezone.now() - timedelta(seconds=10)
            ).first()

            if recent_movement:
                logger.warning(f"⚠️ Mouvement en double détecté: {recent_movement.id}")
                # On pourrait lever une erreur ou simplement continuer
                # Pour le moment, on continue mais on loggue

            # 3. CRÉER LE MOUVEMENT
            # Le signal post_save va décrémenter le stock
            movement = serializer.save(performed_by=self.request.user)
            
            logger.info(f"✅ Mouvement {movement.id} créé: {movement_type} de {quantity} unités")
            
            return movement

    def perform_update(self, serializer):
        """
        Mise à jour d'un mouvement - NE PAS AUTORISER pour éviter les incohérences
        """
        raise ValidationError("La modification des mouvements de stock n'est pas autorisée")

    def perform_destroy(self, instance):
        """
        Suppression d'un mouvement - NE PAS AUTORISER
        """
        raise ValidationError("La suppression des mouvements de stock n'est pas autorisée")


class OutOfStockView(APIView):
    """
    Liste des médicaments en rupture avec recommandation de commande
    """
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
            # Calcul du stock actuel
            current_stock = StockLot.objects.filter(
                medicine=med,
                expiry_date__gte=date.today()
            ).aggregate(total=Sum('quantity'))['total'] or 0

            # Ventes moyennes sur 30 jours
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            avg_sales = SaleItem.objects.filter(
                medicine=med,
                sale__created_at__date__gte=thirty_days_ago
            ).aggregate(avg=Avg('quantity'))['avg'] or 0

            # Suggestion de commande
            simple_suggestion = max(med.max_stock - current_stock, 0)
            ai_suggestion = max(int(avg_sales * 7), 0)  # 7 jours de stock
            recommended = max(simple_suggestion, ai_suggestion)

            if recommended == 0:
                recommended = med.max_stock

            data.append({
                'id': med.id,
                'name': med.commercial_name,
                'category': med.category.name if med.category else '',
                'current_stock': current_stock,
                'avg_daily_sales': round(avg_sales, 1),
                'recommended_order': recommended,
                'status': 'RUPTURE' if current_stock == 0 else 'CRITIQUE'
            })

        return Response(data)


class InventorySummaryView(APIView):
    """
    Résumé des stocks pour la page Stock.
    """
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
                status_label = 'Rupture'
            elif remaining < med['min_stock']:
                status = 'LOW'
                status_label = 'Stock faible'
            elif remaining > med['max_stock']:
                status = 'OVER'
                status_label = 'Surstock'
            else:
                status = 'OK'
                status_label = 'Normal'
                
            # Calcul du nombre de jours de stock restant
            avg_daily_sales = SaleItem.objects.filter(
                medicine_id=med['id'],
                sale__created_at__date__gte=today - timedelta(days=30)
            ).aggregate(avg=Avg('quantity'))['avg'] or 1  # Éviter division par zéro
            
            days_remaining = int(remaining / avg_daily_sales) if avg_daily_sales > 0 else 0
            
            data.append({
                'id': med['id'],
                'commercial_name': med['commercial_name'],
                'min_stock': med['min_stock'],
                'max_stock': med['max_stock'],
                'remaining_stock': remaining,
                'status': status,
                'status_label': status_label,
                'days_remaining': days_remaining,
                'avg_daily_sales': round(avg_daily_sales, 1)
            })
            
        return Response(data)


class StockAdjustmentView(APIView):
    """
    Vue pour ajuster manuellement le stock (inventaire)
    """
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def post(self, request):
        """
        Ajustement manuel du stock
        Body: {
            "medicine_id": "...",
            "lot_id": "...",
            "new_quantity": 100,
            "reason": "Inventaire",
            "movement_type": "IN"  # ou "OUT"
        }
        """
        with transaction.atomic():
            medicine_id = request.data.get('medicine_id')
            lot_id = request.data.get('lot_id')
            new_quantity = request.data.get('new_quantity')
            reason = request.data.get('reason', 'Ajustement manuel')
            movement_type = request.data.get('movement_type', 'IN')
            
            try:
                lot = StockLot.objects.select_for_update().get(id=lot_id)
            except StockLot.DoesNotExist:
                return Response(
                    {"error": f"Lot {lot_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculer la différence
            diff = new_quantity - lot.quantity
            
            if diff == 0:
                return Response(
                    {"message": "Aucune modification nécessaire"},
                    status=status.HTTP_200_OK
                )
            
            # Créer un mouvement pour l'ajustement
            movement = StockMovement.objects.create(
                medicine=lot.medicine,
                lot=lot,
                quantity=abs(diff),
                movement_type=movement_type if diff > 0 else 'OUT',
                reason=f"{reason} (Ajustement)",
                performed_by=request.user,
                notes=f"Ancien stock: {lot.quantity}, Nouveau: {new_quantity}"
            )
            
            logger.info(f"✅ Ajustement stock: {lot.medicine.commercial_name} - {diff:+d} unités")
            
            return Response({
                "message": "Stock ajusté avec succès",
                "movement_id": movement.id,
                "old_quantity": lot.quantity - diff,
                "new_quantity": lot.quantity,
                "difference": diff
            })