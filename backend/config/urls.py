# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from apps.reporting.views import sales_report, stock_report, alert_report, user_report

# ========== HEALTH CHECK ==========
def health_check(request):
    return JsonResponse({"status": "ok", "message": "DENG PHARMA API is running"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),  # <--- NOUVEAU
    path('api/', include('apps.medicines.urls')),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/sales/', include('apps.sales.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/reports/sales/', sales_report, name='report-sales'),
    path('api/reports/stock/', stock_report, name='report-stock'),
    path('api/reports/alerts/', alert_report, name='report-alerts'),
    path('api/reports/users/', user_report, name='report-users'),
    path('api/ai/', include('apps.ai_integration.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)