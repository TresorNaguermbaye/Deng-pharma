from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from django.shortcuts import get_object_or_404

from .models import Sale
from .serializers import SaleCreateSerializer, SaleListSerializer
from apps.accounts.permissions import AuditeurReadOnly

class CanCreateSale(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method == 'POST':
            return request.user.role != 'AUDITEUR'
        return True

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.prefetch_related('items__medicine').all()
    permission_classes = [permissions.IsAuthenticated, AuditeurReadOnly, CanCreateSale]

    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        return SaleListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, pk=None):
        sale = self.get_object()
        if request.query_params.get('format') == 'pdf':
            return self.generate_pdf(sale)
        serializer = SaleCreateSerializer(sale)
        return Response(serializer.data)

    def generate_pdf(self, sale):
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
        """Vue fonctionnelle pour générer la facture PDF"""
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