from rest_framework import serializers
from products.models import Category
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    '''product_count = serializers.SerializerMethodField()'''

    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'slug', 
            'description', 
            'parent',
            'status',
            'order',
            'children',
            #'product_count'
        ]
        read_only_fields = ['slug', 'order']

    def get_children(self, obj):
        children = obj.children.order_by('order')
        return CategorySerializer(children, many=True, context=self.context)

    '''def get_product_count(self, obj):
        """Count products in this category and its descendants"""
        category_and_descendants = obj.get_descendants(include_self=True)
        return Product.objects.filter(category__in=category_and_descendants).count()'''

class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'name', 
            'description', 
            'parent', 
            'status',
            'top_level_category'
        ]
        extra_kwargs = {
            'top_level_category': {'required': False},
            'parent': {'required': False}
        }

    def validate(self, data):
        if not data.get('parent') and not data.get('top_level_category'):
            raise serializers.ValidationError(
                "Either parent or top_level_category must be provided"
            )
        
        if data.get('parent') and data.get('top_level_category'):
            raise serializers.ValidationError(
                "Cannot provide both parent and top_level_category"
            )

        # Check hierarchy depth
        if data.get('parent'):
            parent = data['parent']
            if parent.parent and parent.parent.parent:
                raise serializers.ValidationError(
                    "Cannot create category deeper than third level"
                )

        return data
'''

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
        
        return product'''