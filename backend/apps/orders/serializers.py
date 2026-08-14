from rest_framework import serializers
from .models import PurchaseOrder
from apps.medicines.models import Medicine, Supplier
from apps.inventory.models import StockLot, StockMovement

class PurchaseOrderSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.commercial_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'medicine', 'medicine_name', 'supplier', 'supplier_name', 
                  'quantity_ordered', 'status', 'created_by', 'created_at', 'notes']
        read_only_fields = ['created_by', 'created_at', 'status']

    def validate_quantity_ordered(self, value):
        if value <= 0:
            raise serializers.ValidationError("La quantité commandée doit être positive.")
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

# Sérialiseur séparé pour la réception de commande
class PurchaseOrderReceiveSerializer(serializers.Serializer):
    batch_number = serializers.CharField(max_length=100)
    expiry_date = serializers.DateField()
    purchase_price_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    quantity_received = serializers.IntegerField(min_value=1)