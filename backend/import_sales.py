# backend/import_sales.py
import csv
import os
from datetime import datetime, timedelta
from django.utils import timezone
from apps.medicines.models import Medicine, Category
from apps.inventory.models import StockLot, StockMovement
from apps.sales.models import Sale, SaleItem

CSV_PATH = os.path.join(os.path.expanduser("~"), "DENG_PHARMA", "ai_service", "training", "tchad_pharma_sales.csv")

if not os.path.exists(CSV_PATH):
    print(f"❌ Fichier introuvable : {CSV_PATH}")
else:
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📂 {len(rows)} lignes à traiter.")

    category_cache = {}
    med_by_name = {m.commercial_name: m for m in Medicine.objects.all()}

    # Stock initial très élevé pour éviter les ruptures pendant l'import
    initial_stock = 100_000

    for row in rows:
        med_name = row["medicine_name"]
        if med_name not in med_by_name:
            cat_name = row.get("category") or "Général"
            if cat_name not in category_cache:
                cat, _ = Category.objects.get_or_create(name=cat_name)
                category_cache[cat_name] = cat
            else:
                cat = category_cache[cat_name]

            med = Medicine.objects.create(
                commercial_name=med_name,
                dci=row.get("medicine_id", med_name[:20]),
                barcode=f"CSV-{row['medicine_id']}",
                category=cat,
                selling_price=float(row.get("price", 0)),
                purchase_price=float(row.get("price", 0)) / 2,
                min_stock=10,
                max_stock=initial_stock,
            )
            med_by_name[med_name] = med

            # Créer un lot avec un stock initial énorme
            StockLot.objects.create(
                medicine=med,
                batch_number=f"LOT-INITIAL-{row['medicine_id']}",
                quantity=initial_stock,
                expiry_date=timezone.localdate() + timedelta(days=365),
                purchase_price_per_unit=float(row.get("price", 0)) / 2,
            )
        else:
            med = med_by_name[med_name]

        try:
            sale_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            sale_datetime = timezone.make_aware(datetime.combine(sale_date, datetime.min.time()))
        except Exception as e:
            print(f"⚠️ Erreur de date pour {row}, passage")
            continue

        quantity = int(float(row["sales"]))

        sale = Sale.objects.create(
            customer_name="Client généré",
            discount=0,
            total_amount=quantity * float(row.get("price", 0)),
            payment_method="CASH",
            created_at=sale_datetime,
            user_id=1,
        )

        # Sélectionner un lot avec assez de stock (FIFO)
        lot = StockLot.objects.filter(
            medicine=med,
            quantity__gte=quantity,
            expiry_date__gte=timezone.localdate()
        ).order_by('expiry_date').first()

        if not lot:
            # Si aucun lot ne peut satisfaire la quantité, en créer un nouveau avec suffisamment de stock
            lot = StockLot.objects.create(
                medicine=med,
                batch_number=f"LOT-{row['medicine_id']}-{sale_date}",
                quantity=max(initial_stock, quantity),
                expiry_date=timezone.localdate() + timedelta(days=365),
                purchase_price_per_unit=float(row.get("price", 0)) / 2,
            )

        # Créer l'item de vente (sans décrémenter manuellement)
        SaleItem.objects.create(
            sale=sale,
            medicine=med,
            lot=lot,
            quantity=quantity,
            unit_price=float(row.get("price", 0)),
        )

        # Créer le mouvement de stock : le signal post_save décrémentera le lot
        StockMovement.objects.create(
            medicine=med,
            lot=lot,
            movement_type='OUT',
            reason='SALE',
            quantity=quantity,
            reference=f"Vente #{sale.id}",
            performed_by_id=1,
        )

    print("✅ Importation terminée.")