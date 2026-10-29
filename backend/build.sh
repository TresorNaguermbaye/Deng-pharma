#!/usr/bin/env bash
# build.sh — Exécuté automatiquement par Render au déploiement

set -e

echo "🚀 === BUILD DENG PHARMA BACKEND ==="

# 1. Installe les dépendances
pip install -r requirements.txt

# 2. Applique les migrations
python manage.py migrate

# 3. Crée le superuser
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='TresorAdmin').exists():
    User.objects.create_superuser(
        username='TresorAdmin',
        email='tresornaguermbaye@gmail.com',
        password='william1112'
    )
    print('✅ Superuser créé')
else:
    print('⏭️ Superuser existe déjà')
"

# 4. Remplit les catégories et médicaments avec des UUID FIXES
python manage.py shell -c "
from apps.medicines.models import Category, Medicine
from decimal import Decimal
import uuid

# --- CATÉGORIES ---
categories_data = [
    ('Antalgique', 'Médicaments contre la douleur'),
    ('Antibiotique', 'Médicaments contre les infections bactériennes'),
    ('Antipaludéen', 'Médicaments contre le paludisme'),
    ('Réhydratation', 'Solutions de réhydratation orale'),
    ('Anti-inflammatoire', 'Médicaments anti-inflammatoires'),
    ('Antihistaminique', 'Médicaments contre les allergies'),
    ('Antiseptique', 'Produits antiseptiques'),
    ('Vitamine', 'Suppléments vitaminiques'),
    ('Antiparasitaire', 'Médicaments contre les parasites'),
]

for name, desc in categories_data:
    cat, created = Category.objects.get_or_create(
        name=name,
        defaults={'description': desc}
    )
    if created:
        print(f'✅ Catégorie : {name}')

# --- MÉDICAMENTS AVEC UUID FIXES ---
# On crée des UUID déterministes à partir du barcode
# ex: MED001 -> UUID basé sur md5('MED001')
import hashlib

def uuid_from_string(s):
    # Génère un UUID v5 déterministe à partir d'une chaîne
    return uuid.uuid5(uuid.NAMESPACE_DNS, s)

medicaments_data = [
    ('MED001', 'Paracétamol 500mg', 'Paracétamol', 'Antalgique', 'Sanofi', 750, 1500, 100, 5000, 'Rayon A1'),
    ('MED002', 'Amoxicilline 500mg', 'Amoxicilline', 'Antibiotique', 'GSK', 1800, 3500, 50, 2000, 'Rayon B2'),
    ('MED003', 'Arthéméther 20mg', 'Arthéméther', 'Antipaludéen', 'Novartis', 1200, 2500, 50, 2000, 'Rayon C1'),
    ('MED004', 'SRO (Sel Réhydratation)', 'Sels de réhydratation', 'Réhydratation', 'UNICEF', 250, 500, 200, 5000, 'Rayon D1'),
    ('MED005', 'Ibuprofène 400mg', 'Ibuprofène', 'Anti-inflammatoire', 'Pfizer', 600, 1200, 100, 3000, 'Rayon A2'),
    ('MED006', 'Cétirizine 10mg', 'Cétirizine', 'Antihistaminique', 'UCB', 400, 800, 100, 3000, 'Rayon E1'),
    ('MED007', 'Bétadine', 'Povidone iodée', 'Antiseptique', 'Meda Pharma', 450, 900, 50, 2000, 'Rayon F1'),
    ('MED008', 'Ceftriaxone 1g', 'Ceftriaxone', 'Antibiotique', 'Roche', 2200, 4500, 20, 1000, 'Rayon B3'),
    ('MED009', 'Artéméther-Luméfantrine', 'Artéméther + Luméfantrine', 'Antipaludéen', 'Novartis', 1600, 3200, 50, 2000, 'Rayon C2'),
    ('MED010', 'Vitamine C 500mg', 'Acide ascorbique', 'Vitamine', 'Bayer', 300, 600, 200, 5000, 'Rayon G1'),
    ('MED011', 'Mébendazole 100mg', 'Mébendazole', 'Antiparasitaire', 'Janssen', 350, 700, 100, 3000, 'Rayon H1'),
    ('MED012', 'Diclofénac 50mg', 'Diclofénac', 'Anti-inflammatoire', 'Novartis', 1000, 2000, 50, 2000, 'Rayon A3'),
    ('MED013', 'Ciprofloxacine 500mg', 'Ciprofloxacine', 'Antibiotique', 'Bayer', 1400, 2800, 50, 2000, 'Rayon B4'),
    ('MED014', 'Sérum oral', 'Solution de réhydratation', 'Réhydratation', 'UNICEF', 200, 450, 200, 5000, 'Rayon D2'),
    ('MED015', 'Artésunate 60mg', 'Artésunate', 'Antipaludéen', 'Guilin Pharma', 900, 1800, 50, 2000, 'Rayon C3'),
]

for barcode, name, dci, cat_name, manufacturer, purchase_price, selling_price, min_stock, max_stock, location in medicaments_data:
    cat = Category.objects.get(name=cat_name)
    fixed_uuid = uuid_from_string(barcode)

    med, created = Medicine.objects.get_or_create(
        barcode=barcode,
        defaults={
            'id': fixed_uuid,
            'commercial_name': name,
            'dci': dci,
            'category': cat,
            'manufacturer': manufacturer,
            'purchase_price': Decimal(str(purchase_price)),
            'selling_price': Decimal(str(selling_price)),
            'min_stock': min_stock,
            'max_stock': max_stock,
            'location': location,
        }
    )
    if created:
        print(f'✅ {barcode} ({fixed_uuid}) - {name}')
    else:
        print(f'⏭️ Existe déjà : {barcode}')

print(f'\\n🎉 Total : {Medicine.objects.count()} médicaments')
"

echo "🎯 === BUILD TERMINÉ ==="