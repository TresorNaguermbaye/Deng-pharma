from rest_framework import serializers
from datetime import date
from .models import Sale, SaleItem
from apps.medicines.models import Medicine
from apps.inventory.models import StockLot

class SaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.commercial_name', read_only=True)

    class Meta:
        model = SaleItem
        fields = ['id', 'medicine', 'medicine_name', 'quantity', 'unit_price']

class SaleCreateSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = ['id', 'customer_name', 'discount', 'payment_method', 'items', 'total_amount', 'created_at']
        read_only_fields = ['id','total_amount', 'created_at']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Une vente doit contenir au moins un article.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        # Calcul du total hors remise
        total = sum(item['quantity'] * item['unit_price'] for item in items_data)
        discount = validated_data.get('discount', 0)
        total_amount = total - discount
        validated_data['total_amount'] = total_amount
        # Sauvegarde de la vente
        sale = Sale.objects.create(**validated_data)
        # Création des items et mise à jour du stock
        for item_data in items_data:
            medicine = item_data['medicine']
            quantity = item_data['quantity']
            # Sélection du lot en FEFO
            lot = StockLot.objects.filter(
                medicine=medicine,
                quantity__gt=0,
                expiry_date__gte=date.today()
            ).order_by('expiry_date').first()
            if not lot:
                raise serializers.ValidationError(f"Stock insuffisant pour {medicine.commercial_name}")
            if lot.quantity < quantity:
                raise serializers.ValidationError(f"Quantité insuffisante dans le lot {lot.batch_number} pour {medicine.commercial_name}")
            # Créer l'item
            SaleItem.objects.create(sale=sale, medicine=medicine, lot=lot, quantity=quantity, unit_price=item_data['unit_price'])
            # Décrémenter le lot
            lot.quantity -= quantity
            lot.save(update_fields=['quantity'])
            # Enregistrer le mouvement de stock
            from apps.inventory.models import StockMovement
            StockMovement.objects.create(
                medicine=medicine,
                lot=lot,
                movement_type='OUT',
                reason='SALE',
                quantity=quantity,
                reference=f"Vente #{sale.id}",
                performed_by=sale.user
            )
        return sale

class SaleListSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour la liste des ventes"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Sale
        fields = ['id', 'user', 'user_email', 'customer_name', 'total_amount', 'payment_method', 'created_at']