from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import date

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer, PurchaseOrderReceiveSerializer
from apps.inventory.models import StockLot, StockMovement

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('medicine', 'supplier', 'created_by')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Réceptionner une commande : crée le lot et le mouvement de stock"""
        order = self.get_object()
        if order.status != 'PENDING':
            return Response({"detail": "Cette commande ne peut pas être reçue."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PurchaseOrderReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            lot = StockLot.objects.create(
                medicine=order.medicine,
                batch_number=data['batch_number'],
                quantity=data['quantity_received'],
                expiry_date=data['expiry_date'],
                purchase_price_per_unit=data['purchase_price_per_unit'],
            )
            StockMovement.objects.create(
                medicine=order.medicine,
                lot=lot,
                movement_type='IN',
                reason='PURCHASE',
                quantity=data['quantity_received'],
                reference=f"Commande #{order.id}",
                performed_by=request.user
            )
            order.status = 'RECEIVED'
            order.save(update_fields=['status'])

        return Response({"detail": "Commande reçue et stock mis à jour."})

    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        """Télécharge le bon de commande en PDF."""
        order = self.get_object()
        html_string = render_to_string('orders/purchase_order.html', {'order': order})
        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bon_commande_{order.id}.pdf"'
        return response
