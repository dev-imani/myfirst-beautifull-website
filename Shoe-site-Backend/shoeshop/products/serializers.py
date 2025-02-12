from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from products.choices import BaseProductStatusChoices, CategoryChoices, CategoryStatusChoices
from products.models import BaseProduct, Brand, Category, ClothingProduct, ClothingVariant, ProductImage, ShoeColor, ShoeProduct, ShoeSize, ShoeVariant



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


class BrandSerializer(serializers.ModelSerializer):
    """
    Serializer for the Brand model.

    This serializer converts Brand model instances into JSON format and vice versa.
    It includes the following fields:
    - id: The unique identifier for the brand.
    - name: The name of the brand.
    - description: A brief description of the brand.
    - popularity: The popularity rating of the brand.
    """
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description', 'popularity']

        read_only_fields = ['id', 'popularity']
        extra_kwargs = {
                'name': {'required': True},
                'description': {'required': True},
            }
        
class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.
    
    Fields:
        id (int): The unique identifier for the image
        image (str): The image file path/URL
        alt_text (str): Alternative text for the image
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']

class ShoeSizeSerializer(serializers.ModelSerializer):
    """
    Serializer for shoe sizes.
    
    Fields:
        id (int): The unique identifier for the size
        size (str): The shoe size value
    """
    class Meta:
        model = ShoeSize
        fields = ['id', 'size']

class ShoeColorSerializer(serializers.ModelSerializer):
    """
    Serializer for shoe colors.
    
    Fields:
        id (int): The unique identifier for the color
        color (str): The color name
        image (str): Image representing the color
    """
    class Meta:
        model = ShoeColor
        fields = ['id', 'color', 'image']

class ShoeVariantSerializer(serializers.ModelSerializer):
    """
    Serializer for shoe variants (combination of size and color).
    
    Fields:
        id (int): The unique identifier for the variant
        size (str): The shoe size
        color (str): The color name
        stock (int): Available stock for this variant
    """
    class Meta:
        model = ShoeVariant
        fields = ['id', 'size', 'color', 'stock']

    def validate(self, data):
        """
        Validate that the size and color combination is valid for the product.
        
        Args:
            data (dict): The variant data containing size and color

        Returns:
            dict: Validated data if all checks pass

        Raises:
            ValidationError: If size or color is not available for the product
        """
        product = self.context.get('product')
        if not product:
            raise ValidationError("Product context is required for variant validation")

        size_name = data.get('size')
        color_name = data.get('color')

        available_sizes = product.sizes.values_list('size', flat=True)
        available_colors = product.colors.values_list('color', flat=True)

        if size_name and size_name.lower() not in (s.lower() for s in available_sizes):
            raise ValidationError({"size": f"Size '{size_name}' is not available for this product."})

        if color_name and color_name.lower() not in (c.lower() for c in available_colors):
            raise ValidationError({"color": f"Color '{color_name}' is not available for this product."})

        if data.get('stock', 0) < 0:
            raise ValidationError({"stock": "Stock cannot be negative."})

        return data

class BaseProductSerializer(serializers.ModelSerializer):
    """
    Base serializer for all product types.
    
    This serializer handles common product attributes and provides basic validation
    for fields that are shared across all product types.
    
    Fields:
        id (int): The unique identifier for the product
        name (str): Product name
        description (str): Product description
        price (decimal): Product price
        brand (int): Brand ID
        brand_name (str): Brand name (read-only)
        category (int): Category ID
        category_name (str): Category name (read-only)
        sku (str): Stock Keeping Unit
        status (str): Product status
        stock (int): Total available stock
        images (list): List of product images
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    images = ProductImageSerializer(many=True, required=False)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)

       class Meta:
        model = BaseProduct
        fields = [
            'id', 'name', 'description', 'price', 'brand', 'brand_name',
            'category', 'category_name', 'sku', 'status', 'stock',
            'images', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'price': {'required': True},
            'stock': {'required': True},
        }

    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise ValidationError("Price must be greater than zero")
        return value

    def validate_stock(self, value):
        """Validate that stock is not negative."""
        if value < 0:
            raise ValidationError("Stock cannot be negative")
        return value

    def validate_status(self, value):
        """Validate that status is one of the allowed values."""
        if value.lower() not in (status.lower() for status in BaseProductStatusChoices.choices):
            raise ValidationError(f"Status must be one of {', '.join(CategoryStatusChoices.values)}")
        return value.lower()

class ShoeProductSerializer(BaseProductSerializer):
    """
    Serializer for shoe products, extending the base product serializer.
    
    Additional Fields:
        gender (str): Target gender for the shoe
        size_type (str): Type of size system used
        material (str): Shoe material
        style (str): Shoe style
        variants (list): List of size/color combinations
        sizes (list): Available sizes
        colors (list): Available colors
    """
    
    sizes = ShoeSizeSerializer(many=True, required=False)
    colors = ShoeColorSerializer(many=True, required=False)
    variants = ShoeVariantSerializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        model = ShoeProduct
        fields = BaseProductSerializer.Meta.fields + [
            'gender', 'size_type', 'material', 'style', 'variants', 'sizes', 'colors'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new shoe product with its related objects (sizes, colors, variants).
        
        Args:
            validated_data (dict): The validated data for creating the product

        Returns:
            ShoeProduct: The created shoe product instance
        """
        sizes_data = validated_data.pop('sizes', [])
        colors_data = validated_data.pop('colors', [])
        variants_data = validated_data.pop('variants', [])
        images_data = validated_data.pop('images', [])

        # Create the main product
        product = ShoeProduct.objects.create(**validated_data)

        # Bulk create related objects
        self._create_sizes(product, sizes_data)
        self._create_colors(product, colors_data)
        self._create_variants(product, variants_data)
        self._create_images(product, images_data)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update a shoe product and its related objects.
        
        Args:
            instance (ShoeProduct): The existing product instance
            validated_data (dict): The validated data for updating

        Returns:
            ShoeProduct: The updated shoe product instance
        """
        sizes_data = validated_data.pop('sizes', None)
        colors_data = validated_data.pop('colors', None)
        variants_data = validated_data.pop('variants', None)
        images_data = validated_data.pop('images', None)

        # Update main product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update related objects if provided
        if sizes_data is not None:
            self._update_sizes(instance, sizes_data)
        if colors_data is not None:
            self._update_colors(instance, colors_data)
        if variants_data is not None:
            self._update_variants(instance, variants_data)
        if images_data is not None:
            self._update_images(instance, images_data)

        return instance

    def _create_sizes(self, product, sizes_data):
        """Bulk create sizes for a product."""
        ShoeSize.objects.bulk_create([
            ShoeSize(product=product, **size_data)
            for size_data in sizes_data
        ])

    def _create_colors(self, product, colors_data):
        """Bulk create colors for a product."""
        ShoeColor.objects.bulk_create([
            ShoeColor(product=product, **color_data)
            for color_data in colors_data
        ])

    def _create_variants(self, product, variants_data):
        """Create variants with validation."""
        for variant_data in variants_data:
            variant_serializer = ShoeVariantSerializer(
                data=variant_data, 
                context={'product': product}
            )
            variant_serializer.is_valid(raise_exception=True)
            variant_serializer.save(product=product)

    def _create_images(self, product, images_data):
        """Bulk create images for a product."""
        ProductImage.objects.bulk_create([
            ProductImage(product=product, **image_data)
            for image_data in images_data
        ])

    def _update_sizes(self, product, sizes_data):
        """Update sizes for a product."""
        product.sizes.all().delete()
        self._create_sizes(product, sizes_data)

    def _update_colors(self, product, colors_data):
        """Update colors for a product."""
        product.colors.all().delete()
        self._create_colors(product, colors_data)

    def _update_variants(self, product, variants_data):
        """Update variants for a product."""
        product.variants.all().delete()
        self._create_variants(product, variants_data)

    def _update_images(self, product, images_data):
        """Update images for a product."""
        product.images.all().delete()
        self._create_images(product, images_data)

class ClothingVariantSerializer(serializers.ModelSerializer):
    """
    Serializer for clothing variants.
    
    Fields:
        id (int): The unique identifier for the variant
        size (str): The clothing size
        stock (int): Available stock for this variant
    """
    class Meta:
        model = ClothingVariant
        fields = ['id', 'size', 'stock']

    def validate_stock(self, value):
        """Validate that stock is not negative."""
        if value < 0:
            raise ValidationError("Stock cannot be negative")
        return value

class ClothingProductSerializer(BaseProductSerializer):
    """
    Serializer for clothing products, extending the base product serializer.
    
    Additional Fields:
        material (str): Clothing material
        color (str): Color of the clothing item
        variants (list): List of size variants
    """
    variants = ClothingVariantSerializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        model = ClothingProduct
        fields = BaseProductSerializer.Meta.fields + [
            'material', 'color', 'variants'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new clothing product with its related objects.
        
        Args:
            validated_data (dict): The validated data for creating the product

        Returns:
            ClothingProduct: The created clothing product instance
        """
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])

        product = ClothingProduct.objects.create(**validated_data)
        
        self._create_images(product, images_data)
        self._create_variants(product, variants_data)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update a clothing product and its related objects.
        
        Args:
            instance (ClothingProduct): The existing product instance
            validated_data (dict): The validated data for updating

        Returns:
            ClothingProduct: The updated clothing product instance
        """
        images_data = validated_data.pop('images', None)
        variants_data = validated_data.pop('variants', None)

        # Update main product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update related objects if provided
        if images_data is not None:
            self._update_images(instance, images_data)
        if variants_data is not None:
            self._update_variants(instance, variants_data)

        return instance

    def _create_images(self, product, images_data):
        """Bulk create images for a product."""
        ProductImage.objects.bulk_create([
            ProductImage(product=product, **image_data)
            for image_data in images_data
        ])

    def _create_variants(self, product, variants_data):
        """Bulk create variants for a product."""
        ClothingVariant.objects.bulk_create([
            ClothingVariant(product=product, **variant_data)
            for variant_data in variants_data
        ])

    def _update_images(self, product, images_data):
        """Update images for a product."""
        product.images.all().delete()
        self._create_images(product, images_data)

    def _update_variants(self, product, variants_data):
        """Update variants for a product."""
        product.variants.all().delete()
        self._create_variants(product, variants_data)