import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command

print("🔄 Chargement des données...")
try:
    call_command('loaddata', 'data_dump.json', ignore_nonexistent=True)
    print("✅ Données chargées avec succès !")
except Exception as e:
    print(f"❌ Erreur: {e}")