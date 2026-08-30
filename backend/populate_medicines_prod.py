import os
import django
import sys
import random
from datetime import datetime, timedelta

# Configuration pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.medicines.models import Medicine, Category
from apps.inventory.models import StockLot, StockMovement
from django.contrib.auth import get_user_model
from django.db import transaction

print("🚀 Peuplement direct de la base de production...")

# Récupérer ou créer un utilisateur pour les mouvements
User = get_user_model()
user, created = User.objects.get_or_create(
    username='system',
    defaults={
        'email': 'system@dengpharma.com',
        'is_active': True,
    }
)
if created:
    user.set_password('system123')
    user.save()
    print("✅ Utilisateur système créé")

# Données des catégories
categories_data = [
    ('Antalgiques', 'Médicaments contre la douleur'),
    ('Antibiotiques', 'Lutte contre les infections bactériennes'),
    ('Antipaludéens', 'Traitement du paludisme'),
    ('Anti-inflammatoires', "Réduction de l'inflammation"),
    ('Antihistaminiques', 'Traitement des allergies'),
    ('Vaccins', 'Prévention des maladies'),
    ('Vitamines', 'Compléments nutritionnels'),
    ('Antiparasitaires', 'Lutte contre les parasites'),
    ('Antiacides', "Traitement des brûlures d'estomac"),
    ('Antitussifs', 'Traitement de la toux'),
]

# Données des médicaments avec prix ajustés
medicines_data = [
    # (commercial_name, dci, barcode, category_name, purchase_price, selling_price, location, min_stock, max_stock, manufacturer, initial_quantity)
    
    # Antalgiques
    ('Paracétamol 500mg', 'Paracétamol', 'BAR001', 'Antalgiques', 650, 1800, 'Rayon A1', 20, 200, 'LaboPharm', 1200),
    ('Paracétamol 1000mg', 'Paracétamol', 'BAR002', 'Antalgiques', 950, 2500, 'Rayon A1', 15, 150, 'LaboPharm', 900),
    ('Ibuprofène 400mg', 'Ibuprofène', 'BAR003', 'Anti-inflammatoires', 950, 2000, 'Rayon A2', 15, 150, 'MediLab', 1100),
    ('Ibuprofène 600mg', 'Ibuprofène', 'BAR004', 'Anti-inflammatoires', 1350, 2800, 'Rayon A2', 10, 100, 'MediLab', 850),
    ('Diclofénac 50mg', 'Diclofénac', 'BAR005', 'Anti-inflammatoires', 550, 1200, 'Rayon A3', 20, 200, 'PharmaCare', 1300),
    
    # Antibiotiques
    ('Amoxicilline 500mg', 'Amoxicilline', 'BAR006', 'Antibiotiques', 1350, 2800, 'Rayon B1', 25, 250, 'BioLab', 1100),
    ('Amoxicilline 1g', 'Amoxicilline', 'BAR007', 'Antibiotiques', 1950, 3800, 'Rayon B1', 20, 200, 'BioLab', 900),
    ('Azithromycine 250mg', 'Azithromycine', 'BAR008', 'Antibiotiques', 1650, 3500, 'Rayon B2', 20, 200, 'MediLab', 1000),
    ('Azithromycine 500mg', 'Azithromycine', 'BAR009', 'Antibiotiques', 2650, 5200, 'Rayon B2', 15, 150, 'MediLab', 850),
    ('Ciprofloxacine 500mg', 'Ciprofloxacine', 'BAR010', 'Antibiotiques', 2150, 4200, 'Rayon B3', 20, 200, 'BioLab', 950),
    
    # Antipaludéens
    ('Artéméther 20mg', 'Artéméther', 'BAR011', 'Antipaludéens', 950, 2200, 'Rayon C1', 30, 300, 'PharmaCare', 1400),
    ('Artéméther 40mg', 'Artéméther', 'BAR012', 'Antipaludéens', 1650, 3800, 'Rayon C1', 20, 200, 'PharmaCare', 1000),
    ('Quinine 300mg', 'Quinine', 'BAR013', 'Antipaludéens', 1150, 2800, 'Rayon C2', 20, 200, 'LaboPharm', 1100),
    ('Quinine 600mg', 'Quinine', 'BAR014', 'Antipaludéens', 1950, 4200, 'Rayon C2', 15, 150, 'LaboPharm', 850),
    
    # Antihistaminiques
    ('Cétirizine 10mg', 'Cétirizine', 'BAR015', 'Antihistaminiques', 450, 900, 'Rayon E1', 20, 200, 'MediLab', 1500),
    ('Loratadine 10mg', 'Loratadine', 'BAR016', 'Antihistaminiques', 500, 1000, 'Rayon E2', 15, 150, 'MediLab', 1200),
    ('Fexofénadine 120mg', 'Fexofénadine', 'BAR017', 'Antihistaminiques', 750, 1600, 'Rayon E2', 15, 150, 'PharmaCare', 1000),
    
    # Vaccins
    ('Vaccin Méningite', 'Méningocoque', 'BAR018', 'Vaccins', 4200, 8500, 'Rayon F1', 10, 50, 'BioLab', 800),
    ('Vaccin Grippe', 'Influenza', 'BAR019', 'Vaccins', 3200, 6500, 'Rayon F2', 10, 50, 'BioLab', 900),
    ('Vaccin Rougeole', 'Rougeole', 'BAR020', 'Vaccins', 2700, 5500, 'Rayon F2', 10, 50, 'BioLab', 850),
    
    # Vitamines
    ('Vitamine C 1000mg', 'Acide ascorbique', 'BAR021', 'Vitamines', 300, 600, 'Rayon G1', 30, 300, 'PharmaCare', 1800),
    ('Vitamine D 1000 UI', 'Cholécalciférol', 'BAR022', 'Vitamines', 500, 1000, 'Rayon G1', 20, 200, 'PharmaCare', 1200),
    ('Oméga 3 1000mg', 'Acides gras', 'BAR023', 'Vitamines', 750, 1600, 'Rayon G2', 20, 200, 'MediLab', 1000),
    
    # Antiparasitaires
    ('Métronidazole 250mg', 'Métronidazole', 'BAR024', 'Antiparasitaires', 1150, 2200, 'Rayon H1', 20, 200, 'BioLab', 1100),
    ('Métronidazole 500mg', 'Métronidazole', 'BAR025', 'Antiparasitaires', 1950, 3800, 'Rayon H1', 15, 150, 'BioLab', 900),
    
    # Antiacides
    ('Oméprazole 20mg', 'Oméprazole', 'BAR026', 'Antiacides', 650, 1350, 'Rayon I1', 20, 200, 'MediLab', 1300),
    ('Oméprazole 40mg', 'Oméprazole', 'BAR027', 'Antiacides', 950, 2200, 'Rayon I1', 15, 150, 'MediLab', 1000),
    ('Ranéprine 150mg', 'Ranéprine', 'BAR028', 'Antiacides', 550, 1150, 'Rayon I2', 20, 200, 'PharmaCare', 1400),
    
    # Antitussifs
    ('Sirop Toux 200ml', 'Dextrométhorphane', 'BAR029', 'Antitussifs', 1650, 3200, 'Rayon J1', 15, 150, 'LaboPharm', 900),
    ('Sirop Toux Enfant', 'Dextrométhorphane', 'BAR030', 'Antitussifs', 1150, 2200, 'Rayon J1', 20, 200, 'LaboPharm', 1100),
]

@transaction.atomic
def populate_medicines():
    """Peuple la base de données avec les médicaments et leurs stocks"""
    
    print("📦 Création des catégories...")
    categories = {}
    for name, desc in categories_data:
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        categories[name] = cat
        if created:
            print(f"  ✅ Catégorie '{name}' créée")
    
    print("\n💊 Création des médicaments et des stocks...")
    created_count = 0
    stock_created = 0
    
    for data in medicines_data:
        commercial_name, dci, barcode, category_name, purchase_price, selling_price, location, min_stock, max_stock, manufacturer, initial_quantity = data
        
        category = categories.get(category_name)
        if not category:
            print(f"  ⚠️ Catégorie '{category_name}' non trouvée pour {commercial_name}")
            continue
        
        # Créer ou récupérer le médicament
        med, created = Medicine.objects.get_or_create(
            barcode=barcode,
            defaults={
                'commercial_name': commercial_name,
                'dci': dci,
                'category': category,
                'purchase_price': purchase_price,
                'selling_price': selling_price,
                'location': location,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'manufacturer': manufacturer,
                'description': f"{commercial_name} - {dci}",
            }
        )
        
        if created:
            created_count += 1
            print(f"  ✅ {commercial_name} créé")
            
            # Créer un lot de stock initial
            expiry_date = datetime.now() + timedelta(days=random.randint(180, 730))
            lot = StockLot.objects.create(
                medicine=med,
                batch_number=f"LOT-{barcode}-INIT",
                quantity=initial_quantity,
                expiry_date=expiry_date,
                received_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                purchase_price_per_unit=purchase_price,
            )
            stock_created += 1
            print(f"     📦 Lot créé: {lot.batch_number} - {initial_quantity} unités")
            
            # Créer un mouvement d'entrée initial
            StockMovement.objects.create(
                medicine=med,
                lot=lot,
                movement_type='IN',
                reason='PURCHASE',
                quantity=initial_quantity,
                reference="Stock initial",
                performed_by=user,
            )
            print(f"     📊 Mouvement d'entrée enregistré")
    
    print(f"\n✅ {created_count} médicaments créés avec succès !")
    print(f"📦 {stock_created} lots de stock créés")
    print(f"📊 Total: {Medicine.objects.count()} médicaments")
    print(f"📊 Total lots: {StockLot.objects.count()}")

if __name__ == "__main__":
    try:
        populate_medicines()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)