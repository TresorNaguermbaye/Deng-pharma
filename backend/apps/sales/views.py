# apps/sales/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from datetime import date
import hashlib
import hmac
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.accounts.permissions import CanManageSales
from .models import Sale, SaleItem
from .serializers import SaleCreateSerializer, SaleListSerializer
from apps.inventory.models import StockLot, StockMovement


import logging

# Configuration du logger
logger = logging.getLogger(__name__)


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
    total_str = f"{float(total):.2f}"
    data = f"{sale_id}:{total_str}"
        
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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Création d'une vente avec application FEFO
        ✅ CORRECTION : La décrémentation du stock est gérée UNIQUEMENT par le signal
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        # 1. CRÉER LA VENTE
        sale = Sale.objects.create(
            user=user,
            customer_name=data.get('customer_name'),
            discount=data.get('discount', 0),
            total_amount=0,
            payment_method=data.get('payment_method', 'CASH')
        )

        total = 0
        items_data = data.get('items', [])

        # 2. TRAITER CHAQUE ITEM
        for item_data in items_data:
            medicine = item_data.get('medicine')
            quantity = item_data.get('quantity')
            unit_price = item_data.get('unit_price')

            # ✅ APPLICATION FEFO (First Expired First Out)
            # Sélectionner le lot avec la date d'expiration la plus proche
            # select_for_update() verrouille le lot pendant la transaction
            available_lot = StockLot.objects.filter(
                medicine=medicine,
                quantity__gt=0,
                expiry_date__gte=date.today()
            ).select_for_update().order_by('expiry_date').first()

            if not available_lot:
                # Annuler la vente si un produit n'est pas disponible
                sale.delete()
                return Response(
                    {"error": f"Aucun lot disponible pour {medicine.commercial_name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. CRÉER L'ITEM DE VENTE
            SaleItem.objects.create(
                sale=sale,
                medicine=medicine,
                lot=available_lot,
                quantity=quantity,
                unit_price=unit_price
            )

            # 4. CRÉER LE MOUVEMENT DE STOCK
            # ✅ UNIQUEMENT le mouvement de stock (pas de décrémentation manuelle)
            # Le signal post_save de StockMovement va :
            #    - Décrémenter le stock (lot.quantity -= quantity)
            #    - Déclencher les notifications (rupture, stock faible)
            #    - Envoyer les emails et push notifications
            StockMovement.objects.create(
                medicine=medicine,
                lot=available_lot,
                movement_type='OUT',
                reason='SALE',
                quantity=quantity,
                reference=f"Vente #{sale.id}",
                performed_by=user
            )
            
            logger.info(f"✅ Vente #{sale.id} - {medicine.commercial_name}: {quantity} unités sorties")

            total += quantity * unit_price

        # 5. METTRE À JOUR LE TOTAL
        sale.total_amount = total - sale.discount
        sale.save()

        # 6. RÉCUPÉRER LES DÉTAILS FEFO POUR LA RÉPONSE
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

        logger.info(f"✅ Vente #{sale.id} créée avec succès - Total: {sale.total_amount} FCFA")

        return Response({
            "id": sale.id,
            "total": sale.total_amount,
            "discount": sale.discount,
            "payment_method": sale.payment_method,
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
        
        expected_signature = generate_invoice_signature(sale.id, sale.total_amount)
        
        # ✅ LOGS POUR VOIR LES SIGNATURES
        logger.info(f"🔍 Vérification facture #{sale.id}")
        logger.info(f"   Signature reçue: '{signature}'")
        logger.info(f"   Signature attendue: '{expected_signature}'")
        logger.info(f"   Total: {sale.total_amount} (type: {type(sale.total_amount).__name__})")
        
        is_valid = signature == expected_signature
        
        return Response({
            'id': sale.id,
            'date': sale.created_at,
            'total': sale.total_amount,
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