from django.conf import settings
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from products.choices import CategoryChoices, CategoryStatusChoices
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
        """
        Retrieves the children of a given object based on the specified depth in the context.
        Args:
            obj: The object for which to retrieve children.
        Returns:
            list: A list of serialized children objects.
        Behavior:
            - If the depth is 0, returns an empty list but still serializes the parent.
            - If the depth is None, returns all descendants of the object.
            - If the depth is 1, returns immediate children without their children field.
            - If the depth is greater than 1, includes children recursively, decreasing the depth by 1 for each level.
        """
        current_depth = self.context.get("depth", None)
    
        # If depth is 0, return empty children list
        if current_depth == 0:
            return []
            
        # If depth is None, return all descendants
        if current_depth is None:
            children = obj.get_descendants().order_by('order')
            return CategorySerializer(children, many=True, context=self.context).data
            
        # Get only immediate children for depth=1
        if current_depth == 1:
            children = obj.get_children().order_by('order')
            # Use a different serializer context that will return no children
            return CategorySerializer(
                children, 
                many=True, 
                context={**self.context, "depth": 0}  # Force children to have depth=0
            ).data
        
        # For depth>1, get immediate children and recurse with depth-1
        children = obj.get_children().order_by('order')
        if children:
            return CategorySerializer(
                children,
                many=True,
                context={**self.context, "depth": current_depth - 1}
            ).data
        return []
    '''  def get_product_count(self, obj):

        """Count products in this category and its descendants"""

        category_and_descendants = obj.get_descendants(include_self=True)

        return Product.objects.filter(category__in=category_and_descendants).count()''' 

class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating Category instances.
    Meta:
        model: The model associated with this serializer (Category).
        fields: List of fields to be included in the serialized representation.
        extra_kwargs: Additional keyword arguments for specific fields.
        read_only_fields: Fields that are read-only.
    Methods:
        validate(data):
            Validates the input data for creating or updating a Category instance.
            Ensures that either 'parent' or 'top_level_category' is provided.
            Validates the 'top_level_category' against allowed choices.
            Ensures the category does not exceed the maximum depth set in settings.
            Raises ValidationError for any invalid conditions.
        create(validated_data):
            Creates a new Category instance with the validated data.
            Sets the 'name' and 'slug' fields for top-level categories.
        update(instance, validated_data):
            Updates an existing Category instance with the validated data.
            Prevents modification of 'top_level_category' and top-level category 'name'.
            Ensures the new parent is a valid category and not the same as the instance.
    """
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
        '''if data.get('parent') and not data.get('name'):
            raise ValidationError("Name is required", code="required")'''
        
        if data.get('top_level_category'):
            top_level_category_lower = data['top_level_category'].lower()
            if top_level_category_lower not in [choice.lower() for choice in CategoryChoices.values]:
                raise ValidationError(
                    f"Invalid top_level_category '{data['top_level_category']}'. Available choices are: {', '.join([choice[1] for choice in CategoryChoices.choices])}."
                )
            data['top_level_category'] = top_level_category_lower
            if Category.objects.filter(top_level_category=data['top_level_category']).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(
                    f"A category with top_level_category '{data['top_level_category']}' already exists."
                )
        
        if not self.instance:  # Create operation
            if not data.get('parent') and not data.get('top_level_category'):
                raise ValidationError("Either parent or top_level_category must be provided")
        else:  # Update operation
            if data.get('parent') and data.get('top_level_category'):
                raise ValidationError("Cannot provide both parent and top_level_category")
        
        # Enforce maximum depth if a parent is provided
        max_depth = getattr(settings, "CATEGORY_MAX_DEPTH", 3)
        if data.get('parent'):
            parent = data['parent']
            depth = 1
            while parent:
                parent = parent.parent
                depth += 1
                if depth > max_depth:
                    raise ValidationError(f"Cannot create category deeper than {max_depth} levels.")
        
        return data

    def create(self, validated_data):
        if not validated_data.get('parent'):
            top_level_category_lower = validated_data['top_level_category'].lower()
            validated_data['name'] = top_level_category_lower.capitalize()
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle status updates
        if 'status' in validated_data:
            new_status = validated_data['status']
            if new_status not in CategoryStatusChoices.values:
                raise ValidationError(
                    f"Invalid status. Allowed statuses are: {', '.join(CategoryStatusChoices.values)}."
                )
            if instance.status != new_status:
                instance.status = new_status

        # Prevent modification of top-level category fields for categories without a parent.
        if instance.parent is None and 'name' in validated_data:
            raise ValidationError("Top-level category name cannot be updated.")
        if instance.parent is None and 'parent' in validated_data:
            raise ValidationError("Top-level category parent cannot be updated.")
        if 'top_level_category' in validated_data:
            raise ValidationError("Top-level category cannot be updated.")
        
        # Update the name and regenerate slug if provided.
        if 'name' in validated_data:
            instance.name = validated_data['name']
            instance.slug = slugify(instance.name)

        # Validate new parent assignment.
        new_parent = validated_data.get('parent')
        if new_parent:
            if new_parent == instance:
                raise ValidationError("A category cannot be its own parent.")
            if new_parent.parent is None:
                raise ValidationError("Cannot assign a top-level category as a parent.")
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