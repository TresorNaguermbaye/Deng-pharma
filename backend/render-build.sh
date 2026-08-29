#!/bin/bash
set -o errexit

echo "🚀 Début du build sur Render..."

# Vérifier que le fichier data_dump_final.json existe
if [ -f "data_dump_final.json" ]; then
    echo "✅ data_dump_final.json trouvé ! Taille : $(ls -lh data_dump_final.json | awk '{print $5}')"
else
    echo "❌ data_dump_final.json INTROUVABLE !"
    exit 1
fi

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "📂 Exécution des migrations..."
python manage.py migrate --noinput

echo "📊 Chargement des données depuis data_dump_final.json (signaux désactivés)..."
python manage.py shell <<EOF
from django.core.management import call_command
from django.db import connection
from django.apps import apps

# Désactiver les signaux
for app_config in apps.get_app_configs():
    app_config._signal_handlers = []

call_command('loaddata', 'data_dump_final.json', ignorenonexistent=True)
EOF

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput