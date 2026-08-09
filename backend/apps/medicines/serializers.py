from rest_framework import serializers
from .models import Category, Medicine

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class MedicineListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Medicine
        fields = [
            'id', 'commercial_name', 'dci', 'barcode',
            'category', 'category_name', 'selling_price',
            'image', 'location', 'min_stock', 'max_stock',
            'created_at', 'updated_at'
        ]

class MedicineDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    purchase_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

    class Meta:
        model = Medicine
        fields = '__all__'