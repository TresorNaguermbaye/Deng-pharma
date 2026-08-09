from django.urls import path
from .views import SalesReportView, StockReportView, AlertReportView, UserReportView

urlpatterns = [
    path('sales/', SalesReportView.as_view(), name='report-sales'),
    path('stock/', StockReportView.as_view(), name='report-stock'),
    path('alerts/', AlertReportView.as_view(), name='report-alerts'),
    path('users/', UserReportView.as_view(), name='report-users'),
]