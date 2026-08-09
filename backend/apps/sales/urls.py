from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, invoice_pdf

router = DefaultRouter()
router.register(r'sales', SaleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('sales/<int:sale_id>/invoice/', invoice_pdf, name='sale-invoice'),
]