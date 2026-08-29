#!/bin/bash
set -o errexit

echo "🚀 Début du build sur Render..."

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "📂 Exécution des migrations..."
python manage.py migrate --noinput

echo "📊 Chargement des données depuis data_dump_final_clean.json..."
python manage.py loaddata data_dump_final_clean.json --ignorenonexistent

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Build terminé avec succès !"