from datetime import date, datetime, timedelta, time as dtime
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.sales.models import Sale, SaleItem
from apps.medicines.models import Medicine, Category
from apps.inventory.models import StockLot
from apps.accounts.permissions import AuditeurReadOnly
from django.db.models.functions import Coalesce

from django.db.models.functions import TruncDate

class TodaySalesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = timezone.localdate()
        sales = Sale.objects.filter(created_at__date=today).prefetch_related('items__medicine').order_by('-created_at')
        data = []
        for sale in sales:
            items = [{
                'medicine': item.medicine.commercial_name,
                'quantity': item.quantity,
                'price': float(item.unit_price)
            } for item in sale.items.all()]
            data.append({
                'id': sale.id,
                'customer': sale.customer_name or 'Comptoir',
                'total': float(sale.total_amount),
                'payment': sale.get_payment_method_display(),
                'time': sale.created_at.strftime('%H:%M'),
                'items': items
            })
        return Response(data)

class OutOfStockView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        medicines = Medicine.objects.all()
        out = []
        for med in medicines:
            total = StockLot.objects.filter(medicine=med, expiry_date__gte=today).aggregate(t=Sum('quantity'))['t'] or 0
            if total == 0:
                out.append({
                    'id': med.id,
                    'name': med.commercial_name,
                    'category': med.category.name if med.category else '',
                    'min_stock': med.min_stock,
                    'current_stock': 0,
                    'recommended_order': med.min_stock * 2 if med.min_stock else 30
                })
        return Response(out)

class LowStockView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        medicines = Medicine.objects.all()
        low = []
        for med in medicines:
            total = StockLot.objects.filter(medicine=med, expiry_date__gte=today).aggregate(t=Sum('quantity'))['t'] or 0
            if 0 < total <= med.min_stock:
                low.append({
                    'id': med.id,
                    'name': med.commercial_name,
                    'category': med.category.name if med.category else '',
                    'min_stock': med.min_stock,
                    'current_stock': total,
                    'to_order': med.min_stock * 2 - total
                })
        return Response(low)

class ExpiringSoonView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        limit = today + timedelta(days=90)
        lots = StockLot.objects.filter(expiry_date__lte=limit, expiry_date__gte=today, quantity__gt=0).select_related('medicine').order_by('expiry_date')
        data = []
        for lot in lots:
            data.append({
                'id': lot.id,
                'medicine': lot.medicine.commercial_name,
                'batch': lot.batch_number,
                'quantity': lot.quantity,
                'expiry_date': lot.expiry_date.isoformat(),
                'days_left': (lot.expiry_date - today).days
            })
        return Response(data)



class DashboardKPIView(APIView):
    """Retourne les indicateurs clés pour le tableau de bord principal"""
    permission_classes = [IsAuthenticated, AuditeurReadOnly]

    def get(self, request):
        today = timezone.localdate()
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


        # Nouvelle version (cohérente avec OutOfStockView)
        out_of_stock_count = 0
        for med in Medicine.objects.all():
            total = StockLot.objects.filter(medicine=med, expiry_date__gte=today).aggregate(t=Sum('quantity'))['t'] or 0
            if total == 0:
                out_of_stock_count += 1


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

class SalesChartView(APIView):
    permission_classes = [IsAuthenticated, AuditeurReadOnly]

    def get(self, request):
        # 1. Calculer la plage des 7 derniers jours en heure locale
        today_local = timezone.localdate()
        start_local = today_local - timedelta(days=6)

        # Convertir en datetime local minuit et en UTC pour le filtre
        start_datetime_local = datetime.combine(start_local, dtime.min)
        end_datetime_local = datetime.combine(today_local, dtime.max)

        start_utc = timezone.make_aware(start_datetime_local, timezone.get_current_timezone())
        end_utc = timezone.make_aware(end_datetime_local, timezone.get_current_timezone())

        # Récupérer toutes les ventes sur la période (filtrées en UTC)
        sales = Sale.objects.filter(created_at__range=(start_utc, end_utc)).only('created_at', 'total_amount')

        # Initialiser les agrégats pour chaque jour
        daily_sales = []
        for i in range(6, -1, -1):
            day = today_local - timedelta(days=i)
            daily_sales.append({
                'date': day.isoformat(),
                'day_name': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'][day.weekday()],
                'revenue': 0.0,
                'orders': 0,
                '_count': 0,
            })

        # Remplir avec les ventes réelles en convertissant en heure locale
        for sale in sales:
            local_time = timezone.localtime(sale.created_at)
            local_date = local_time.date()
            day_index = (local_date - start_local).days
            if 0 <= day_index <= 6:
                daily_sales[day_index]['revenue'] += float(sale.total_amount)
                daily_sales[day_index]['orders'] += 1
                daily_sales[day_index]['_count'] += 1

        # Supprimer le champ temporaire _count
        for item in daily_sales:
            del item['_count']

        # 2. Top médicaments (inchangé)
        top_meds = SaleItem.objects.values('medicine__commercial_name').annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_qty')[:10]

        top_medicines = [{
            'name': item['medicine__commercial_name'],
            'quantity': item['total_qty'],
            'revenue': float(item['total_revenue'])
        } for item in top_meds]

        # 3. Ventes par catégorie (inchangé)
        cat_sales = SaleItem.objects.values('medicine__category__name').annotate(
            total=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total')

        categories = [{
            'name': item['medicine__category__name'] or 'Sans catégorie',
            'revenue': float(item['total'])
        } for item in cat_sales]

        return Response({
            'daily_sales': daily_sales,
            'top_medicines': top_medicines,
            'categories': categories
        })


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'medicines': [], 'sales': [], 'customers': []})

        # Recherche médicaments
        medicines = Medicine.objects.filter(
            Q(commercial_name__icontains=query) |
            Q(dci__icontains=query) |
            Q(barcode__icontains=query)
        )[:10]
        medicine_data = [{
            'id': str(med.id),
            'commercial_name': med.commercial_name,
            'dci': med.dci,
            'category_name': med.category.name if med.category else '',
            'selling_price': float(med.selling_price),
        } for med in medicines]

        # Recherche ventes par ID ou nom client
        sales_qs = Sale.objects.filter(
            Q(customer_name__icontains=query) |
            (Q(id__icontains=query) if query.isdigit() else Q())
        ).select_related('user')[:10]
        sales_data = [{
            'id': sale.id,
            'customer_name': sale.customer_name or 'Client comptoir',
            'total_amount': float(sale.total_amount),
            'payment_method': sale.get_payment_method_display(),
            'created_at': sale.created_at.strftime('%d/%m/%Y %H:%M'),
        } for sale in sales_qs]

        # Recherche clients distincts (basé sur customer_name non vide)
        customers_qs = Sale.objects.exclude(customer_name__isnull=True).exclude(customer_name='').filter(
            customer_name__icontains=query
        ).values('customer_name').distinct()[:10]
        customers_data = [{'name': item['customer_name']} for item in customers_qs]

        return Response({
            'medicines': medicine_data,
            'sales': sales_data,
            'customers': customers_data,
        })