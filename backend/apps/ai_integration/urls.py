# apps/ai_integration/urls.py
from django.urls import path
from .views import (
    AIPredictView,
    AIRecommendStockView,
    AIStockAnalysisView,
    AIOrderRecommendationView,
    AISeasonalAnalysisView,
    AICriticalityView,
    AIChatView,
    AIHealthView,
)

urlpatterns = [
    # Prédictions
    path('predict/', AIPredictView.as_view(), name='ai-predict'),
    
    # Analyse de stock
    path('stock-analysis/', AIStockAnalysisView.as_view(), name='ai-stock-analysis'),
    
    # Recommandation de commande
    path('order-recommendation/', AIOrderRecommendationView.as_view(), name='ai-order-recommendation'),
    
    # Analyse saisonnière
    path('seasonal/', AISeasonalAnalysisView.as_view(), name='ai-seasonal'),
    
    # Score de criticité
    path('criticality/', AICriticalityView.as_view(), name='ai-criticality'),
    
    # Chatbot
    path('chat/', AIChatView.as_view(), name='ai-chat'),

    path('recommend-stock/', AIRecommendStockView.as_view(), name='ai-recommend-stock'),
    
    # Santé du service
    path('health/', AIHealthView.as_view(), name='ai-health'),
]