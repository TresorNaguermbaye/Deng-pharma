import os
import django
import sys
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.medicines.models import Medicine, Category
from apps.inventory.models import StockLot, StockMovement
from django.contrib.auth import get_user_model
from django.db import transaction

print("🚀 Peuplement des lots de stock pour tous les médicaments...")

User = get_user_model()
user = User.objects.first()
if not user:
    user = User.objects.create_superuser('system', 'system@dengpharma.com', 'system123')
    print("✅ Superutilisateur système créé")

@transaction.atomic
def populate_stocks():
    """Crée des lots de stock pour tous les médicaments"""
    
    medicines = Medicine.objects.all()
    print(f"📊 {medicines.count()} médicaments trouvés")
    
    created_count = 0
    for med in medicines:
        # Vérifier si le médicament a déjà des lots
        existing_lots = StockLot.objects.filter(medicine=med)
        if existing_lots.exists():
            print(f"  ⏭️ {med.commercial_name} a déjà {existing_lots.count()} lots, ignoré")
            continue
        
        # Créer un lot pour ce médicament
        initial_quantity = random.randint(800, 1800)
        expiry_date = datetime.now() + timedelta(days=random.randint(180, 730))
        
        lot = StockLot.objects.create(
            medicine=med,
            batch_number=f"LOT-{med.barcode}-INIT",
            quantity=initial_quantity,
            expiry_date=expiry_date,
            received_date=datetime.now() - timedelta(days=random.randint(1, 30)),
            purchase_price_per_unit=med.purchase_price,
        )
        created_count += 1
        print(f"  ✅ {med.commercial_name}: {initial_quantity} unités ajoutées")
        
        # Créer un mouvement d'entrée
        StockMovement.objects.create(
            medicine=med,
            lot=lot,
            movement_type='IN',
            reason='PURCHASE',
            quantity=initial_quantity,
            reference="Stock initial",
            performed_by=user,
        )
    
    print(f"\n✅ {created_count} lots de stock créés !")
    print(f"📦 Total lots: {StockLot.objects.count()}")

if __name__ == "__main__":
    try:
        populate_stocks()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)