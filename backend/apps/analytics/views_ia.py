from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ai_client import ai_client  # import de votre client singleton

class IAPredictView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        medicine_id = request.query_params.get('medicine_id')
        days = request.query_params.get('days', 7)
        if not medicine_id:
            return Response({"error": "medicine_id est requis"}, status=400)
        try:
            result = ai_client.predict_sales(medicine_id, days_ahead=int(days))
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class IAStockAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        medicine_id = request.query_params.get('medicine_id')
        current_stock = request.query_params.get('current_stock')
        if not medicine_id or current_stock is None:
            return Response({"error": "medicine_id et current_stock sont requis"}, status=400)
        try:
            result = ai_client.analyze_stock(medicine_id, float(current_stock))
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class IAOrderRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        medicine_id = request.query_params.get('medicine_id')
        current_stock = request.query_params.get('current_stock')
        if not medicine_id or current_stock is None:
            return Response({"error": "medicine_id et current_stock sont requis"}, status=400)
        try:
            result = ai_client.recommend_order(medicine_id, float(current_stock))
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class IASeasonalAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            result = ai_client.get_seasonal_analysis()
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class IACriticalityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        medicine_id = request.query_params.get('medicine_id')
        if not medicine_id:
            return Response({"error": "medicine_id est requis"}, status=400)
        try:
            result = ai_client.get_criticality(medicine_id)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class IAModelPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            result = ai_client.get_model_performance()
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class IAShapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        medicine_id = request.query_params.get('medicine_id')
        if not medicine_id:
            return Response({"error": "medicine_id est requis"}, status=400)
        try:
            result = ai_client.get_shap_analysis(medicine_id)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
class TrainModelView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        try:
            result = ai_client.train_model()
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
