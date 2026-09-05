from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from datetime import date

from apps.accounts.permissions import CanManageSales, AuditeurReadOnly
from .models import Sale, SaleItem
from .serializers import SaleCreateSerializer, SaleListSerializer
from apps.inventory.models import StockLot, StockMovement


class CanCreateSale(permissions.BasePermission):
    """Permission : seul un AUDITEUR ne peut pas créer de vente"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method == 'POST':
            return request.user.role != 'AUDITEUR'
        return True


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les ventes avec :
    - Création avec application FEFO
    - Génération de PDF
    - Récupération des détails FEFO
    """
    queryset = Sale.objects.prefetch_related('items__medicine').all()
    permission_classes = [IsAuthenticated, CanManageSales]

    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        return SaleListSerializer

    def perform_create(self, serializer):
        """Sauvegarde la vente avec l'utilisateur connecté"""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Création d'une vente avec :
        - Application FEFO (First Expired, First Out)
        - Mise à jour des lots de stock
        - Création des mouvements de stock
        - Retour des détails FEFO
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        # 1. Créer la vente
        sale = Sale.objects.create(
            user=user,
            customer_name=data.get('customer_name'),
            discount=data.get('discount', 0),
            total_amount=0,
            payment_method=data.get('payment_method', 'CASH')
        )

        total = 0
        items_data = data.get('items', [])

        # 2. Pour chaque article, appliquer FEFO
        for item_data in items_data:
            medicine = item_data.get('medicine')
            quantity = item_data.get('quantity')
            unit_price = item_data.get('unit_price')

            # ✅ APPLICATION FEFO : Sélectionner le lot avec la date d'expiration la plus proche
            available_lot = StockLot.objects.filter(
                medicine=medicine,
                quantity__gt=0,
                expiry_date__gte=date.today()
            ).order_by('expiry_date').first()

            if not available_lot:
                # Si aucun lot disponible, annuler la vente
                sale.delete()
                return Response(
                    {"error": f"Aucun lot disponible pour {medicine.commercial_name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Créer l'article de vente
            sale_item = SaleItem.objects.create(
                sale=sale,
                medicine=medicine,
                lot=available_lot,
                quantity=quantity,
                unit_price=unit_price
            )

            # Réduire le stock du lot
            available_lot.quantity -= quantity
            available_lot.save()

            # Créer un mouvement de stock
            StockMovement.objects.create(
                medicine=medicine,
                lot=available_lot,
                movement_type='OUT',
                reason='SALE',
                quantity=quantity,
                reference=f"Vente #{sale.id}",
                performed_by=user
            )

            total += quantity * unit_price

        # 3. Mettre à jour le total de la vente
        sale.total_amount = total - sale.discount
        sale.save()

        # 4. ✅ RÉCUPÉRER LES DÉTAILS FEFO POUR LA RÉPONSE
        sale_items = SaleItem.objects.filter(sale=sale)
        lot_details = []
        for item in sale_items:
            lot_details.append({
                "medicine_name": item.medicine.commercial_name,
                "quantity": item.quantity,
                "lot_batch": item.lot.batch_number if item.lot else "N/A",
                "expiry_date": item.lot.expiry_date.strftime('%Y-%m-%d') if item.lot else "N/A",
                "remaining_stock": item.lot.quantity if item.lot else 0
            })

        # 5. Réponse avec les détails FEFO
        response_data = {
            "id": sale.id,
            "total": sale.total_amount,
            "lot_details": lot_details  # ← NOUVEAU : récapitulatif FEFO
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Récupère une vente avec ou sans PDF"""
        sale = self.get_object()
        if request.query_params.get('format') == 'pdf':
            return self.generate_pdf(sale)
        serializer = SaleCreateSerializer(sale)
        return Response(serializer.data)

    def generate_pdf(self, sale):
        """Génère la facture PDF d'une vente"""
        items = sale.items.all()
        subtotal = sum(item.quantity * item.unit_price for item in items)
        total = sale.total_amount
        discount = subtotal - total

        context = {
            'sale': sale,
            'items': items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
        }
        html_string = render_to_string('sales/invoice.html', context)
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_{sale.id}.pdf"'
        return response


def invoice_pdf(request, sale_id):
    """Vue fonctionnelle pour générer la facture PDF (endpoint public)"""
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.items.all()
    subtotal = sum(item.quantity * item.unit_price for item in items)
    total = sale.total_amount
    discount = subtotal - total

    context = {
        'sale': sale,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
    }
    html_string = render_to_string('sales/invoice.html', context)
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{sale.id}.pdf"'
    return response