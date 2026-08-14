from django.urls import path
from .views import DashboardKPIView, ExpiringSoonView, LowStockView, SalesChartView, TodaySalesView,OutOfStockView

urlpatterns = [

    path('dashboard/', DashboardKPIView.as_view(), name='dashboard-kpi'),

    path('charts/', SalesChartView.as_view(), name='sales-charts'),

    path('today-sales/', TodaySalesView.as_view(), name='today-sales'),
    path('out-of-stock/', OutOfStockView.as_view(), name='out-of-stock'),
    path('low-stock/', LowStockView.as_view(), name='low-stock'),
    path('expiring-soon/', ExpiringSoonView.as_view(), name='expiring-soon'),

]