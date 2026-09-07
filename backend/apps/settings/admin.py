# apps/settings/admin.py
from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'slogan', 'phone', 'updated_at']
    fieldsets = (
        ('Informations générales', {
            'fields': ('site_name', 'slogan', 'logo')
        }),
        ('Coordonnées', {
            'fields': ('phone', 'address')
        }),
    )