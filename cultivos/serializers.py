from rest_framework import serializers
from .models import Category, Product, Municipality, Sowing

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'category_id']

class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = ['id', 'name']

class SowingSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    municipality = MunicipalitySerializer(read_only=True)
    municipality_id = serializers.PrimaryKeyRelatedField(
        queryset=Municipality.objects.all(), source='municipality', write_only=True
    )

    class Meta:
        model = Sowing
        fields = [
            'id', 'farmer', 'product', 'product_id', 'quantity', 'sowing_date',
            'municipality', 'municipality_id', 'harvest_date', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'farmer']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['farmer'] = request.user
        return super().create(validated_data)