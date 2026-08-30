import os
import django
import sys

# Configuration pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.medicines.models import Medicine, Category
from django.db import transaction

print("🚀 Peuplement direct de la base de production...")

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

# Données des médicaments
medicines_data = [
    # (commercial_name, dci, barcode, category_name, purchase_price, selling_price, location, min_stock, max_stock, manufacturer)
    
    # Antalgiques
    ('Paracétamol 500mg', 'Paracétamol', 'BAR001', 'Antalgiques', 500, 1500, 'Rayon A1', 20, 200, 'LaboPharm'),
    ('Paracétamol 1000mg', 'Paracétamol', 'BAR002', 'Antalgiques', 800, 2500, 'Rayon A1', 15, 150, 'LaboPharm'),
    ('Ibuprofène 400mg', 'Ibuprofène', 'BAR003', 'Anti-inflammatoires', 800, 1800, 'Rayon A2', 15, 150, 'MediLab'),
    ('Ibuprofène 600mg', 'Ibuprofène', 'BAR004', 'Anti-inflammatoires', 1200, 2500, 'Rayon A2', 10, 100, 'MediLab'),
    ('Diclofénac 50mg', 'Diclofénac', 'BAR005', 'Anti-inflammatoires', 400, 1000, 'Rayon A3', 20, 200, 'PharmaCare'),
    
    # Antibiotiques
    ('Amoxicilline 500mg', 'Amoxicilline', 'BAR006', 'Antibiotiques', 1200, 2500, 'Rayon B1', 25, 250, 'BioLab'),
    ('Amoxicilline 1g', 'Amoxicilline', 'BAR007', 'Antibiotiques', 1800, 3500, 'Rayon B1', 20, 200, 'BioLab'),
    ('Azithromycine 250mg', 'Azithromycine', 'BAR008', 'Antibiotiques', 1500, 3500, 'Rayon B2', 20, 200, 'MediLab'),
    ('Azithromycine 500mg', 'Azithromycine', 'BAR009', 'Antibiotiques', 2500, 5000, 'Rayon B2', 15, 150, 'MediLab'),
    ('Ciprofloxacine 500mg', 'Ciprofloxacine', 'BAR010', 'Antibiotiques', 2000, 4000, 'Rayon B3', 20, 200, 'BioLab'),
    
    # Antipaludéens
    ('Artéméther 20mg', 'Artéméther', 'BAR011', 'Antipaludéens', 800, 2000, 'Rayon C1', 30, 300, 'PharmaCare'),
    ('Artéméther 40mg', 'Artéméther', 'BAR012', 'Antipaludéens', 1500, 3500, 'Rayon C1', 20, 200, 'PharmaCare'),
    ('Quinine 300mg', 'Quinine', 'BAR013', 'Antipaludéens', 1000, 2500, 'Rayon C2', 20, 200, 'LaboPharm'),
    ('Quinine 600mg', 'Quinine', 'BAR014', 'Antipaludéens', 1800, 4000, 'Rayon C2', 15, 150, 'LaboPharm'),
    
    # Antihistaminiques
    ('Cétirizine 10mg', 'Cétirizine', 'BAR015', 'Antihistaminiques', 300, 800, 'Rayon E1', 20, 200, 'MediLab'),
    ('Loratadine 10mg', 'Loratadine', 'BAR016', 'Antihistaminiques', 350, 900, 'Rayon E2', 15, 150, 'MediLab'),
    ('Fexofénadine 120mg', 'Fexofénadine', 'BAR017', 'Antihistaminiques', 600, 1500, 'Rayon E2', 15, 150, 'PharmaCare'),
    
    # Vaccins
    ('Vaccin Méningite', 'Méningocoque', 'BAR018', 'Vaccins', 4000, 8000, 'Rayon F1', 10, 50, 'BioLab'),
    ('Vaccin Grippe', 'Influenza', 'BAR019', 'Vaccins', 3000, 6000, 'Rayon F2', 10, 50, 'BioLab'),
    ('Vaccin Rougeole', 'Rougeole', 'BAR020', 'Vaccins', 2500, 5000, 'Rayon F2', 10, 50, 'BioLab'),
    
    # Vitamines
    ('Vitamine C 1000mg', 'Acide ascorbique', 'BAR021', 'Vitamines', 200, 500, 'Rayon G1', 30, 300, 'PharmaCare'),
    ('Vitamine D 1000 UI', 'Cholécalciférol', 'BAR022', 'Vitamines', 400, 900, 'Rayon G1', 20, 200, 'PharmaCare'),
    ('Oméga 3 1000mg', 'Acides gras', 'BAR023', 'Vitamines', 600, 1500, 'Rayon G2', 20, 200, 'MediLab'),
    
    # Antiparasitaires
    ('Métronidazole 250mg', 'Métronidazole', 'BAR024', 'Antiparasitaires', 1000, 2000, 'Rayon H1', 20, 200, 'BioLab'),
    ('Métronidazole 500mg', 'Métronidazole', 'BAR025', 'Antiparasitaires', 1800, 3500, 'Rayon H1', 15, 150, 'BioLab'),
    
    # Antiacides
    ('Oméprazole 20mg', 'Oméprazole', 'BAR026', 'Antiacides', 500, 1200, 'Rayon I1', 20, 200, 'MediLab'),
    ('Oméprazole 40mg', 'Oméprazole', 'BAR027', 'Antiacides', 800, 2000, 'Rayon I1', 15, 150, 'MediLab'),
    ('Ranéprine 150mg', 'Ranéprine', 'BAR028', 'Antiacides', 400, 1000, 'Rayon I2', 20, 200, 'PharmaCare'),
    
    # Antitussifs
    ('Sirop Toux 200ml', 'Dextrométhorphane', 'BAR029', 'Antitussifs', 1500, 3000, 'Rayon J1', 15, 150, 'LaboPharm'),
    ('Sirop Toux Enfant', 'Dextrométhorphane', 'BAR030', 'Antitussifs', 1000, 2000, 'Rayon J1', 20, 200, 'LaboPharm'),
]

@transaction.atomic
def populate_medicines():
    """Peuple la base de données avec les médicaments"""
    
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
    
    print("\n💊 Création des médicaments...")
    created_count = 0
    for data in medicines_data:
        commercial_name, dci, barcode, category_name, purchase_price, selling_price, location, min_stock, max_stock, manufacturer = data
        
        category = categories.get(category_name)
        if not category:
            print(f"  ⚠️ Catégorie '{category_name}' non trouvée pour {commercial_name}")
            continue
        
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
    
    print(f"\n✅ {created_count} médicaments créés avec succès !")
    print(f"📊 Total: {Medicine.objects.count()} médicaments")

if __name__ == "__main__":
    try:
        populate_medicines()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)