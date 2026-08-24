# backend/add_sales.py
from apps.sales.models import Sale, SaleItem
from apps.medicines.models import Medicine
from django.utils import timezone
from datetime import timedelta

med = Medicine.objects.get(id='f5ecbc9d-b9c9-455b-84d1-9e0275faef61')

for i in range(7):  # 7 jours passés
    day = timezone.now() - timedelta(days=i+1)
    existing = Sale.objects.filter(
        items__medicine=med,
        created_at__date=day.date()
    ).exists()
    if existing:
        print(f"Vente déjà présente le {day.date()}")
        continue

    sale = Sale.objects.create(
        customer_name="Test SHAP",
        discount=0,
        total_amount=2 * float(med.selling_price),
        payment_method="CASH",
        user_id=1,
    )
    # Forcer la date rétroactive
    Sale.objects.filter(pk=sale.pk).update(created_at=day)

    SaleItem.objects.create(
        sale=sale,
        medicine=med,
        lot=None,
        quantity=2,
        unit_price=float(med.selling_price),
    )
    print(f"Vente ajoutée le {day.date()}")

print("Terminé")
