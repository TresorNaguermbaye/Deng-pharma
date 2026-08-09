from datetime import date, timedelta
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now

from apps.sales.models import Sale
from apps.medicines.models import Medicine, Category
from apps.inventory.models import StockLot
from apps.accounts.permissions import AuditeurReadOnly

class DashboardKPIView(APIView):
    """Retourne les indicateurs clés pour le tableau de bord principal"""
    permission_classes = [IsAuthenticated, AuditeurReadOnly]

    def get(self, request):
        today = now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        previous_day = today - timedelta(days=1)
        previous_week_start = week_start - timedelta(weeks=1)
        previous_month_start = (month_start - timedelta(days=1)).replace(day=1)

        # CA
        ca_today = Sale.objects.filter(created_at__date=today).aggregate(total=Coalesce(Sum('total_amount'), 0.0, output_field=DecimalField()))['total']
        ca_previous_day = Sale.objects.filter(created_at__date=previous_day).aggregate(total=Coalesce(Sum('total_amount'), 0.0, output_field=DecimalField()))['total']
        ca_week = Sale.objects.filter(created_at__date__gte=week_start).aggregate(total=Coalesce(Sum('total_amount'), 0.0, output_field=DecimalField()))['total']
        ca_previous_week = Sale.objects.filter(created_at__date__gte=previous_week_start, created_at__date__lt=week_start).aggregate(total=Coalesce(Sum('total_amount'), 0.0, output_field=DecimalField()))['total']
        ca_month = Sale.objects.filter(created_at__date__gte=month_start).aggregate(total=Coalesce(Sum('total_amount'), 0.0, output_field=DecimalField()))['total']
        ca_previous_month = Sale.objects.filter(created_at__date__gte=previous_month_start, created_at__date__lt=month_start).aggregate(total=Coalesce(Sum('total_amount'), 0.0, output_field=DecimalField()))['total']

        def evolution(current, previous):
            if previous and previous != 0:
                return round(((current - previous) / previous) * 100, 2)
            return 0.0

        ca_today_evolution = evolution(ca_today, ca_previous_day)
        ca_week_evolution = evolution(ca_week, ca_previous_week)
        ca_month_evolution = evolution(ca_month, ca_previous_month)

        # Valeur stock
        stock_value = StockLot.objects.filter(expiry_date__gte=today).aggregate(
            total=Coalesce(Sum(F('quantity') * F('purchase_price_per_unit')), 0.0, output_field=DecimalField())
        )['total']

        total_medicines = Medicine.objects.count()
        total_categories = Category.objects.count()
        sales_today = Sale.objects.filter(created_at__date=today).count()

        # Ruptures
        out_of_stock_ids = StockLot.objects.filter(expiry_date__gte=today).values('medicine').annotate(total_qty=Sum('quantity')).filter(total_qty=0).values('medicine')
        out_of_stock_count = Medicine.objects.filter(id__in=out_of_stock_ids).count()

        # Stock faible
        low_stock_ids = StockLot.objects.filter(expiry_date__gte=today).values('medicine').annotate(total_qty=Sum('quantity')).filter(total_qty__gt=0, total_qty__lte=F('medicine__min_stock')).values('medicine')
        low_stock_count = Medicine.objects.filter(id__in=low_stock_ids).count()

        # Expiration proche
        soon_expired_count = StockLot.objects.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=90)).values('medicine').distinct().count()

        # Profit
        from apps.inventory.models import StockMovement
        cost_of_sales = StockMovement.objects.filter(movement_type='OUT', reason='SALE', created_at__date__gte=month_start).aggregate(
            total_cost=Coalesce(Sum(F('quantity') * F('lot__purchase_price_per_unit')), 0.0, output_field=DecimalField())
        )['total_cost']
        profit = ca_month - cost_of_sales

        data = {
            'ca_today': ca_today,
            'ca_today_evolution': ca_today_evolution,
            'ca_week': ca_week,
            'ca_week_evolution': ca_week_evolution,
            'ca_month': ca_month,
            'ca_month_evolution': ca_month_evolution,
            'stock_value': stock_value,
            'total_medicines': total_medicines,
            'total_categories': total_categories,
            'sales_today': sales_today,
            'out_of_stock': out_of_stock_count,
            'low_stock': low_stock_count,
            'soon_expired': soon_expired_count,
            'estimated_profit': profit,
        }
        return Response(data)