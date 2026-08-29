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

echo "📊 Chargement des données depuis data_dump_final.json..."
python manage.py loaddata data_dump_final.json --ignorenonexistent

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Build terminé avec succès !"