from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, invoice_pdf, VerifyInvoiceView

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')

urlpatterns = [
    path('', include(router.urls)),
    path('sales/<int:sale_id>/invoice/', invoice_pdf, name='sales-invoice-pdf'),
    path('sales/verify/<int:sale_id>/', VerifyInvoiceView.as_view(), name='verify-invoice'),  # ← CETTE LIGNE DOIT EXISTER
]