from datetime import date
from django.db import models
from rest_framework import serializers
from .models import StockLot, StockMovement

class StockLotSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.commercial_name', read_only=True)
    medicine = serializers.PrimaryKeyRelatedField(
        queryset=StockLot._meta.get_field('medicine').remote_field.model.objects.all()
    )

    class Meta:
        model = StockLot
        fields = [
            'id', 'medicine', 'medicine_name', 'batch_number',
            'quantity', 'expiry_date', 'received_date', 'purchase_price_per_unit'
        ]
        read_only_fields = ['received_date']

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("La quantité ne peut pas être négative.")
        return value

class StockMovementSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.commercial_name', read_only=True)
    lot_batch = serializers.CharField(source='lot.batch_number', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.email', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'medicine', 'medicine_name', 'lot', 'lot_batch',
            'movement_type', 'reason', 'quantity', 'reference',
            'performed_by', 'performed_by_name', 'created_at'
        ]
        read_only_fields = ['performed_by', 'created_at']

    def validate(self, data):
        if data['movement_type'] == 'OUT':
            medicine = data['medicine']
            lot = data.get('lot')
            if lot:
                if lot.medicine != medicine:
                    raise serializers.ValidationError("Le lot sélectionné ne correspond pas au médicament.")
                if lot.quantity < data['quantity']:
                    raise serializers.ValidationError("Quantité insuffisante dans le lot sélectionné.")
            else:
                total_stock = StockLot.objects.filter(
                    medicine=medicine,
                    expiry_date__gte=date.today()
                ).aggregate(total=models.Sum('quantity'))['total'] or 0
                if total_stock < data['quantity']:
                    raise serializers.ValidationError("Stock global insuffisant pour cette sortie.")
        return data
