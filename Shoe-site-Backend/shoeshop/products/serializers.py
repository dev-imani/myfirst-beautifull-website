from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from products.choices import CategoryChoices
from products.models import Category
from django.utils.text import slugify


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
            'id',
            'name',
            'description',
            'parent',
            'order',
            'status',
            'top_level_category'
        ]
        extra_kwargs = {
            'top_level_category': {'required': False},
            'parent': {'required': False},
            'order': {'required': False},
        }

    def validate(self, data):
        if data.get('top_level_category'):
            # Convert the value to lowercase for validation
            top_level_category_lower = data['top_level_category'].lower()

            # Check if the category is valid (using lowercase for comparison)
            if top_level_category_lower not in [choice.lower() for choice in CategoryChoices.values]:
                raise ValidationError(
                    f"Invalid top_level_category '{data['top_level_category']}'. Available choices are: {', '.join([choice[1] for choice in CategoryChoices.choices])}."
                )

            # Normalize to lowercase (for database storage and uniqueness)
            data['top_level_category'] = top_level_category_lower

            if Category.objects.filter(top_level_category=data['top_level_category']).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(
                    f"A category with top_level_category '{data['top_level_category']}' already exists."
                )
        if not data.get('parent') and not data.get('top_level_category'):
            raise ValidationError(
                "Either parent or top_level_category must be provided"
            )

        if data.get('parent') and data.get('top_level_category'):
            raise ValidationError(
                "Cannot provide both parent and top_level_category"
            )

        if data.get('parent'):
            parent = data['parent']
            if parent.parent and parent.parent.parent:
                raise ValidationError(
                    "Cannot create category deeper than third level"
                )

        return data

    def create(self, validated_data):
        if not validated_data.get('parent'):
            top_level_category_lower = validated_data['top_level_category'].lower()
            validated_data['name']  = top_level_category_lower.capitalize()
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

    def update(self, validated_data):
        validated_data['slug'] = slugify(validated_data['name'])
        return super().update(validated_data)
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