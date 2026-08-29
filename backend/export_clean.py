import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core import serializers
from django.contrib.auth import get_user_model
from django.db import connection

# Désactiver les signaux
from django.db.models import signals
from apps.inventory import signals as inventory_signals

# Désactiver les signaux problématiques
signals.post_save.disconnect(inventory_signals.handle_stock_movement)

# Exporter les données
from django.core.management import call_command

print("🔄 Exportation des données...")
with open('data_dump_final_clean.json', 'w') as f:
    call_command('dumpdata', 
                 '--exclude=auth.permission',
                 '--exclude=contenttypes',
                 '--exclude=admin.logentry',
                 '--exclude=sessions.session',
                 '--verbosity=0',
                 stdout=f)

print("✅ Export terminé !")