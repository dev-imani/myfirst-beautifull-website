from django.conf import settings
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from products.choices import CategoryChoices
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

        children = obj.get_descendants().order_by('order')
        if children:
            return CategorySerializer(children, many=True, context=self.context).data
        return []

'''  def get_product_count(self, obj):

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
            'description': {'required': True}
        }
        read_only_fields = ['slug', 'order']



    def validate(self, data):
        if data.get('parent') and not data.get('name'):
            raise ValidationError("Name is required", code="required")
        
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
        if not self.instance:  # If it's a create operation
            if not data.get('parent') and not data.get('top_level_category'):
                raise ValidationError(
                    "Either parent or top_level_category must be provided"
                )
        else:  # If it's an update operation
            # You can decide to allow the absence of both `parent` and `top_level_category` here
            if data.get('parent') and data.get('top_level_category'):
                raise ValidationError(
                    "Cannot provide both parent and top_level_category"
                )

        if data.get('parent') and data.get('top_level_category'):
            raise ValidationError(
                "Cannot provide both parent and top_level_category"
            )

        #Ensures the category does not exceed the maximum depth set in settings.
        
        max_depth = getattr(settings, "CATEGORY_MAX_DEPTH", 3)  # Default to 3 if not set

        if data.get('parent'):
            parent = data['parent']
            depth = 1  # Start at 1 (since parent exists)
            while parent:
                parent = parent.parent
                depth += 1
                if depth > max_depth:
                    raise ValidationError(
                        f"Cannot create category deeper than {max_depth} levels."
                    )


        return data

    def create(self, validated_data):
        if not validated_data.get('parent'):
            top_level_category_lower = validated_data['top_level_category'].lower()
            validated_data['name']  = top_level_category_lower.capitalize()
            validated_data['slug'] = slugify(validated_data['name'])
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Prevent modification of top_level_category other that category
        if instance.parent is None and 'name' in validated_data:
            raise ValidationError("Top-level category name cannot be updated.")
        if 'top_level_category' in validated_data:
            raise ValidationError("Top-level category cannot be updated.")
        
        if 'name' in validated_data:
            instance.name = validated_data['name']
            instance.slug = slugify(instance.name)

        new_parent = validated_data.get('parent')

        # Check if the new parent is a valid category
        if new_parent:
            # Ensure the new parent is not the same category being updated
            if new_parent == instance:
                raise ValidationError("A category cannot be its own parent.")

            # Check for any specific logic, such as ensuring the new parent isn't a top-level category
            if new_parent.parent is None:
                raise ValidationError("Cannot assign a top-level category a parent.")

        # Update the category's parent field if provided
        if new_parent:
            instance.parent = new_parent

        
        return super().update(instance, validated_data)

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