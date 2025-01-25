from rest_framework import serializers
from .models import Product, Brand, ProductStock
from django.utils.text import slugify

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description']

class ProductStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStock
        fields = ['size', 'quantity']

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    stock_sizes = ProductStockSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'brand', 
            'description', 'price', 'color', 
            'status', 'stock_sizes'
        ]
        read_only_fields = ['slug']

    def create(self, validated_data):
        """
        Custom create method to handle stock sizes.
        
        Args:
            validated_data (dict): Validated product data
        
        Returns:
            Product: Created product instance
        """
        stock_sizes = self.context.get('stock_sizes', [])
        
        # Ensure slug is generated
        validated_data['slug'] = slugify(validated_data.get('name', ''))
        
        # Create product
        product = Product.objects.create(**validated_data)
        
        # Create stock entries if provided
        for stock_data in stock_sizes:
            ProductStock.objects.create(
                product=product,
                size=stock_data['size'],
                quantity=stock_data['quantity']
            )
        
        return product