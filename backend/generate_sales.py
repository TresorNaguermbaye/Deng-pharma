# generate_sales.py
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from apps.medicines.models import Medicine
from apps.inventory.models import StockLot, StockMovement
from apps.sales.models import Sale, SaleItem

medicines = list(Medicine.objects.all()[:5])
if len(medicines) < 5:
    print("Il faut au moins 5 médicaments dans la base.")
    exit()

# Vérifier ou créer un lot de stock suffisant pour chaque médicament
for med in medicines:
    total_stock = StockLot.objects.filter(medicine=med, expiry_date__gte=timezone.localdate()).aggregate(total=Sum('quantity'))['total'] or 0
    if total_stock < 500:
        StockLot.objects.create(
            medicine=med,
            batch_number=f"STOCK-{med.id}",
            quantity=500,
            expiry_date=timezone.localdate() + timedelta(days=365),
            purchase_price_per_unit=med.purchase_price,
        )
        print(f"Lot de stock créé pour {med.commercial_name} (500 unités)")

start_date = timezone.localdate() - timedelta(days=30)
sales_created = 0

with transaction.atomic():
    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        for med in medicines:
            num_sales_today = random.randint(0, 3)
            for _ in range(num_sales_today):
                quantity = random.randint(1, 5)
                lot = StockLot.objects.filter(
                    medicine=med,
                    quantity__gte=quantity,
                    expiry_date__gte=timezone.localdate()
                ).order_by('expiry_date').first()
                if not lot:
                    lot = StockLot.objects.create(
                        medicine=med,
                        batch_number=f"STOCK-{med.id}-{current_date}",
                        quantity=500,
                        expiry_date=timezone.localdate() + timedelta(days=365),
                        purchase_price_per_unit=med.purchase_price,
                    )
                sale = Sale.objects.create(
                    customer_name=None,
                    discount=0,
                    total_amount=quantity * med.selling_price,
                    payment_method="CASH",
                    created_at=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    user_id=1,
                )
                SaleItem.objects.create(
                    sale=sale,
                    medicine=med,
                    lot=lot,
                    quantity=quantity,
                    unit_price=med.selling_price,
                )
                # Créer le mouvement de stock ; le signal décrémentera le lot
                StockMovement.objects.create(
                    medicine=med,
                    lot=lot,
                    movement_type='OUT',
                    reason='SALE',
                    quantity=quantity,
                    reference=f"Vente #{sale.id}",
                    performed_by_id=1,
                )
                sales_created += 1

print(f"✅ {sales_created} ventes créées pour les 5 médicaments sur 30 jours.")
