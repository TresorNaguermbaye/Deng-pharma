from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny  # ← AJOUTER CETTE LIGNE
from datetime import date
import hashlib
import hmac
import qrcode
from io import BytesIO
import base64
from django.conf import settings

from apps.accounts.permissions import CanManageSales
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


def generate_invoice_signature(sale_id: int, total: float) -> str:
    """Génère une signature HMAC pour vérifier l'authenticité de la facture"""
    secret = settings.SECRET_KEY
    data = f"{sale_id}:{total}"
    signature = hmac.new(
        secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()[:16]
    return signature


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les ventes avec :
    - Création avec application FEFO
    - Génération de PDF avec QR Code
    - Récupération des détails FEFO
    """
    queryset = Sale.objects.prefetch_related('items__medicine').all()
    permission_classes = [IsAuthenticated, CanManageSales]

    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        return SaleListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Création d'une vente avec application FEFO"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        sale = Sale.objects.create(
            user=user,
            customer_name=data.get('customer_name'),
            discount=data.get('discount', 0),
            total_amount=0,
            payment_method=data.get('payment_method', 'CASH')
        )

        total = 0
        items_data = data.get('items', [])

        for item_data in items_data:
            medicine = item_data.get('medicine')
            quantity = item_data.get('quantity')
            unit_price = item_data.get('unit_price')

            # ✅ APPLICATION FEFO
            available_lot = StockLot.objects.filter(
                medicine=medicine,
                quantity__gt=0,
                expiry_date__gte=date.today()
            ).order_by('expiry_date').first()

            if not available_lot:
                sale.delete()
                return Response(
                    {"error": f"Aucun lot disponible pour {medicine.commercial_name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            SaleItem.objects.create(
                sale=sale,
                medicine=medicine,
                lot=available_lot,
                quantity=quantity,
                unit_price=unit_price
            )

            available_lot.quantity -= quantity
            available_lot.save()

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

        sale.total_amount = total - sale.discount
        sale.save()

        # ✅ Récupérer les détails FEFO
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

        return Response({
            "id": sale.id,
            "total": sale.total_amount,
            "lot_details": lot_details
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        sale = self.get_object()
        if request.query_params.get('format') == 'pdf':
            return self.generate_pdf(sale)
        serializer = SaleCreateSerializer(sale)
        return Response(serializer.data)

    def generate_pdf(self, sale):
        """Génère la facture PDF avec QR Code et signature"""
        items = sale.items.all()
        subtotal = sum(item.quantity * item.unit_price for item in items)
        total = sale.total_amount
        discount = subtotal - total

        # ✅ Générer la signature de vérification
        signature = generate_invoice_signature(sale.id, total)
        
        # ✅ URL de la facture en ligne
        frontend_url = settings.FRONTEND_URL
        invoice_url = f"{frontend_url}/invoices/{sale.id}?sign={signature}"
        
        # ✅ Générer le QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=2,
        )
        qr.add_data(invoice_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#0F1A2C", back_color="white")
        
        # Convertir le QR Code en base64 pour l'HTML
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        context = {
            'sale': sale,
            'items': items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
            'invoice_url': invoice_url,
            'signature': signature,
            'qr_base64': qr_base64,
        }
        
        html_string = render_to_string('sales/invoice.html', context)
        from weasyprint import HTML
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_{sale.id}.pdf"'
        return response


class VerifyInvoiceView(APIView):
    """Vue pour vérifier l'authenticité d'une facture"""
    permission_classes = [AllowAny]

    def get(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        signature = request.query_params.get('sign', '')
        
        # Vérifier la signature
        expected_signature = generate_invoice_signature(sale.id, sale.total_amount)
        is_valid = signature == expected_signature
        
        return Response({
            'id': sale.id,
            'date': sale.created_at,
            'total': sale.total_amount,
            'customer': sale.customer_name or 'Client comptoir',
            'valid': is_valid,
            'message': 'Facture authentique ✅' if is_valid else 'Facture invalide ❌'
        })


def invoice_pdf(request, sale_id):
    """Vue fonctionnelle pour générer la facture PDF"""
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.items.all()
    subtotal = sum(item.quantity * item.unit_price for item in items)
    total = sale.total_amount
    discount = subtotal - total

    signature = generate_invoice_signature(sale.id, total)
    frontend_url = settings.FRONTEND_URL
    invoice_url = f"{frontend_url}/invoices/{sale.id}?sign={signature}"
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=2)
    qr.add_data(invoice_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0F1A2C", back_color="white")
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'sale': sale,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'invoice_url': invoice_url,
        'signature': signature,
        'qr_base64': qr_base64,
    }
    html_string = render_to_string('sales/invoice.html', context)
    from weasyprint import HTML
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{sale.id}.pdf"'
    return response