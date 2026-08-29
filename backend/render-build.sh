#!/bin/bash
set -o errexit

echo "🚀 Début du build sur Render..."

# Vérifier que le fichier data_dump.json existe
if [ -f "data_dump.json" ]; then
    echo "✅ data_dump.json trouvé ! Taille : $(ls -lh data_dump.json | awk '{print $5}')"
else
    echo "❌ data_dump.json INTROUVABLE !"
    exit 1
fi

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "📂 Exécution des migrations..."
python manage.py migrate --noinput

echo "📊 Chargement des données depuis data_dump.json..."
python manage.py loaddata data_dump.json --ignorenonexistent || echo "⚠️ Erreur lors du chargement (ignore)..."

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Build terminé avec succès !"