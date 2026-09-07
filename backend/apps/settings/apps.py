# apps/settings/apps.py
from django.apps import AppConfig

class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.settings'
    verbose_name = 'Paramètres du site'