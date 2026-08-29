import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from pathlib import Path

print("🔄 Chargement des données...")

# Chemin absolu vers le fichier
fixture_path = Path(__file__).parent / 'data_dump.json'

try:
    call_command('loaddata', str(fixture_path), ignorenonexistent=True)
    print("✅ Données chargées avec succès !")
except Exception as e:
    print(f"❌ Erreur: {e}")