# apps/ai_integration/views.py
"""
Endpoints Django qui servent de proxy vers le service IA FastAPI
"""
from apps.inventory.models import StockLot
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ai_client import ai_client




from django.db.models import Sum  # <-- AJOUTER CET IMPORT EN HAUT DU FICHIER
from datetime import date

class AIRecommendStockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Nettoyer l'UUID (supprime espaces, < >)
        medicine_id = request.data.get("medicine_id", "").strip().replace('<', '').replace('>', '')
        if not medicine_id:
            return Response({"error": "medicine_id requis"}, status=400)

        # Appeler le service IA
        prediction = ai_client.predict_sales(medicine_id, days_ahead=30)
        if "error" in prediction:
            return Response(prediction, status=503)

        preds = prediction.get("predictions", [])
        avg_daily_demand = sum(p["predicted_sales"] for p in preds) / len(preds) if preds else 0

        total_stock = StockLot.objects.filter(
            medicine_id=medicine_id,
            expiry_date__gte=date.today()
        ).aggregate(total=Sum('quantity'))['total'] or 0

        recommended = max(0, (avg_daily_demand * 30 * 1.2) - total_stock)

        return Response({
            "medicine_id": medicine_id,
            "avg_daily_demand": round(avg_daily_demand, 1),
            "current_stock": total_stock,
            "recommended_order": round(recommended),
            "coverage_days": 30,
        })



class AIPredictView(APIView):
    """Prévision des ventes par IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        medicine_id = request.data.get('medicine_id', 'MED003')
        days_ahead = request.data.get('days_ahead', 7)
        
        result = ai_client.predict_sales(medicine_id, days_ahead)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(result)

class AIStockAnalysisView(APIView):
    """Analyse de stock par IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        medicine_id = request.data.get('medicine_id')
        current_stock = request.data.get('current_stock')
        
        if not medicine_id or current_stock is None:
            return Response(
                {"error": "medicine_id et current_stock requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = ai_client.analyze_stock(medicine_id, current_stock)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(result)

class AIOrderRecommendationView(APIView):
    """Recommandation de commande par IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        medicine_id = request.data.get('medicine_id')
        current_stock = request.data.get('current_stock')
        lead_time = request.data.get('lead_time_days', 7)
        
        if not medicine_id or current_stock is None:
            return Response(
                {"error": "medicine_id et current_stock requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = ai_client.recommend_order(medicine_id, current_stock, lead_time)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(result)

class AISeasonalAnalysisView(APIView):
    """Analyse saisonnière"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        result = ai_client.get_seasonal_analysis()
        return Response(result)

class AICriticalityView(APIView):
    """Score de criticité"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        medicine_id = request.query_params.get('medicine_id', 'MED003')
        result = ai_client.get_criticality(medicine_id)
        return Response(result)

class AIChatView(APIView):
    """Chatbot assistant IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        message = request.data.get('message', '')
        
        if not message:
            return Response(
                {"reply": "Veuillez poser une question."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = ai_client.chat(message)
        return Response(result)

class AIHealthView(APIView):
    """Vérifie l'état du service IA"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        result = ai_client.health_check()
        return Response(result)