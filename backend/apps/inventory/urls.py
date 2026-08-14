from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OutOfStockView, StockLotViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r'lots', StockLotViewSet)
router.register(r'movements', StockMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
      path('out-of-stock/', OutOfStockView.as_view(), name='out-of-stock'),

]


