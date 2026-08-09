from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rapport_pdf_view import sales_report, stock_report, alert_report, user_report

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.medicines.urls')),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/sales/', include('apps.sales.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/reports/sales/', sales_report, name='report-sales'),
    path('api/reports/stock/', stock_report, name='report-stock'),
    path('api/ai/', include('apps.ai_integration.urls')),
    path('api/reports/alerts/', alert_report, name='report-alerts'),
    path('api/reports/users/', user_report, name='report-users'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)