# backend/create_sales_data.py
import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.medicines.models import Medicine
from apps.inventory.models import StockLot
from apps.sales.models import Sale, SaleItem

User = get_user_model()

print("🚀 Création des données de ventes pour le service IA...")

# Récupérer un utilisateur
user = User.objects.first()
if not user:
    print("❌ Aucun utilisateur trouvé !")
    exit(1)

# Récupérer tous les médicaments
medicines = list(Medicine.objects.all())
if not medicines:
    print("❌ Aucun médicament trouvé !")
    exit(1)

print(f"👤 Utilisateur: {user.username}")
print(f"💊 {len(medicines)} médicaments trouvés")

# Créer des lots de stock pour chaque médicament si nécessaire
for med in medicines:
    if not StockLot.objects.filter(medicine=med).exists():
        StockLot.objects.create(
            medicine=med,
            batch_number=f"LOT-{med.barcode}-INIT",
            quantity=random.randint(100, 500),
            expiry_date=datetime.now() + timedelta(days=365),
            received_date=datetime.now() - timedelta(days=30),
            purchase_price_per_unit=med.purchase_price
        )
        print(f"📦 Lot créé pour {med.commercial_name}")

# Créer des ventes pour les 30 derniers jours
created_sales = 0
for day in range(30, 0, -1):
    sale_date = datetime.now() - timedelta(days=day)
    
    # Choisir 3-8 médicaments aléatoires
    num_meds = random.randint(3, min(8, len(medicines)))
    selected_meds = random.sample(medicines, num_meds)
    
    for med in selected_meds:
        quantity = random.randint(1, 10)
        lot = StockLot.objects.filter(medicine=med).first()
        
        if lot and lot.quantity >= quantity:
            # Créer une vente
            sale = Sale.objects.create(
                user=user,
                customer_name=random.choice(['Mme Dupont', 'M. Martin', 'Mme Petit', 'M. Durand', 'Mme Leroy']),
                discount=0,
                total_amount=quantity * med.selling_price,
                payment_method=random.choice(['CASH', 'CARD', 'MOBILE']),
                created_at=sale_date
            )
            
            # Créer l'article de vente
            SaleItem.objects.create(
                sale=sale,
                medicine=med,
                lot=lot,
                quantity=quantity,
                unit_price=med.selling_price
            )
            
            # Mettre à jour le stock
            lot.quantity -= quantity
            lot.save()
            created_sales += 1
    
    if day % 5 == 0:
        print(f"📊 Jour {day}: {created_sales} ventes créées")

print(f"\n✅ {created_sales} ventes créées avec succès !")
print(f"📊 Total des ventes: {Sale.objects.count()}")
print(f"📦 Total des lots: {StockLot.objects.count()}")