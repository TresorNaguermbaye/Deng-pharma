from django.urls import path

from .views_ia import IACriticalityView, IAModelPerformanceView, IAOrderRecommendationView, IAPredictView, IASeasonalAnalysisView, IAShapView, IAStockAnalysisView, TrainModelView
from .views import DashboardKPIView, ExpiringSoonView, GlobalSearchView, LowStockView, SalesChartView, TodaySalesView,OutOfStockView

urlpatterns = [

    path('dashboard/', DashboardKPIView.as_view(), name='dashboard-kpi'),

    path('charts/', SalesChartView.as_view(), name='sales-charts'),

    path('today-sales/', TodaySalesView.as_view(), name='today-sales'),
    path('out-of-stock/', OutOfStockView.as_view(), name='out-of-stock'),
    path('low-stock/', LowStockView.as_view(), name='low-stock'),
    path('expiring-soon/', ExpiringSoonView.as_view(), name='expiring-soon'),
    # Routes IA
    path('ia/predict/', IAPredictView.as_view(), name='ia-predict'),
    path('ia/stock-analysis/', IAStockAnalysisView.as_view(), name='ia-stock-analysis'),
    path('ia/order-recommendation/', IAOrderRecommendationView.as_view(), name='ia-order-recommendation'),
    path('ia/seasonal/', IASeasonalAnalysisView.as_view(), name='ia-seasonal'),
    path('ia/criticality/', IACriticalityView.as_view(), name='ia-criticality'),
    path('ia/model-performance/', IAModelPerformanceView.as_view(), name='ia-model-performance'),
    path('ia/shap/', IAShapView.as_view(), name='ia-shap'),
    path('search/', GlobalSearchView.as_view(), name='global-search'),
    path('ia/train/', TrainModelView.as_view(), name='ia-train'),
]