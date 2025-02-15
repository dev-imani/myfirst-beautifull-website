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
        
        # For depth > 1, get immediate children and recurse with depth-1
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
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']
        
    def validate(self, data):
        # Check if adding this image would exceed the 3-image limit
        request = self.context.get('request')
        if request and request.method == 'POST':
            product = self.context.get('product')
            if product and product.images.count() >= 3:
                raise ValidationError("Maximum of 3 images allowed per product.")
        return data

class ShoeSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoeSize
        fields = ['id', 'size']

class ShoeColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoeColor
        fields = ['id', 'color']

class ShoeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoeVariant
        fields = ['id', 'size', 'color', 'stock']

    def validate(self, data):
        # Validate stock
        if data.get('stock', 0) < 0:
            raise ValidationError({"stock": "Stock cannot be negative."})
        
        # Validate uniqueness of size/color combination
        request = self.context.get('request')
        if request and request.method == 'POST':
            product = self.context.get('product')
            if product:
                existing = ShoeVariant.objects.filter(
                    product=product,
                    size=data['size'],
                    color=data['color']
                ).exists()
                if existing:
                    raise ValidationError(
                        {"non_field_errors": "This size/color combination already exists."}
                    )
        return data

class BaseProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = None
        fields = [
            'id', 'name', 'description', 'price', 'brand', 'brand_name',
            'prod_type', 'category', 'category_name', 'sku', 'status', 'stock',
            'images', 'created_at', 'updated_at', 'total_stock'
        ]
        read_only_fields = ['sku', 'created_at', 'updated_at', 'total_stock']

    def validate_price(self, value):
        if value <= 0:
            raise ValidationError("Price must be greater than zero")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise ValidationError("Stock cannot be negative")
        return value

    def validate_category(self, value):
        if not value.parent:
            raise ValidationError("Products cannot be assigned to root categories")
        return value

class ShoeProductSerializer(BaseProductSerializer):
    sizes = ShoeSizeSerializer(many=True, required=False)
    colors = ShoeColorSerializer(many=True, required=False)
    variants = ShoeVariantSerializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        model = ShoeProduct
        fields = BaseProductSerializer.Meta.fields + [
            'gender', 'size_type', 'material', 'style', 'variants', 'sizes', 'colors'
        ]
        
    def _process_sizes_and_colors(self, sizes_data, colors_data):
        sizes = []
        colors = []
        
        if sizes_data:
            for size_data in sizes_data:
                size, _ = ShoeSize.objects.get_or_create(size=size_data['size'])
                sizes.append(size)
                
        if colors_data:
            for color_data in colors_data:
                color, _ = ShoeColor.objects.get_or_create(color=color_data['color'])
                colors.append(color)
                
        return sizes, colors

    @transaction.atomic
    def create(self, validated_data):
        # Extract nested data
        sizes_data = validated_data.pop('sizes', [])
        colors_data = validated_data.pop('colors', [])
        variants_data = validated_data.pop('variants', [])
        images_data = validated_data.pop('images', [])

        try:
            # Process sizes and colors first
            sizes, colors = self._process_sizes_and_colors(sizes_data, colors_data)
            # Create the base product without M2M fields first
            product = ShoeProduct.objects.create(**validated_data)
            
            # Now that product has an ID, set M2M relationships
            if sizes:
                product.sizes.set(sizes)
            if colors:
                product.colors.set(colors)

            # Create variants after sizes and colors are set
            available_sizes = {s.size for s in sizes}
            available_colors = {c.color for c in colors}

            # Validate and create variants
            for variant_data in variants_data:
                size = variant_data.get('size')
                color = variant_data.get('color')
                
                if size not in available_sizes:
                    raise ValidationError(f"Size '{size}' is not available for this product.")
                if color not in available_colors:
                    raise ValidationError(f"Color '{color}' is not available for this product.")
                
                ShoeVariant.objects.create(product=product, **variant_data)

            # Handle images
            if images_data:
                if len(images_data) > 3:
                    raise ValidationError("Maximum 3 images allowed per product.")
                
                for image_data in images_data:
                    image = ProductImage.objects.create(**image_data)
                    product.images.add(image)

            return product

        except Exception as e:
            # If anything fails, the transaction will rollback
            raise ValidationError(str(e))

    @transaction.atomic
    def update(self, instance, validated_data):
        sizes_data = validated_data.pop('sizes', None)
        colors_data = validated_data.pop('colors', None)
        variants_data = validated_data.pop('variants', None)
        images_data = validated_data.pop('images', None)

        try:
            # Update main product fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Update sizes and colors if provided
            if sizes_data is not None:
                sizes, _ = self._process_sizes_and_colors(sizes_data, [])
                instance.sizes.set(sizes)

            if colors_data is not None:
                _, colors = self._process_sizes_and_colors([], colors_data)
                instance.colors.set(colors)

            # Update variants if provided
            if variants_data is not None:
                instance.variants.all().delete()
                available_sizes = set(instance.sizes.values_list('size', flat=True))
                available_colors = set(instance.colors.values_list('color', flat=True))

                for variant_data in variants_data:
                    size = variant_data.get('size')
                    color = variant_data.get('color')
                    
                    if size not in available_sizes:
                        raise ValidationError(f"Size '{size}' is not available for this product.")
                    if color not in available_colors:
                        raise ValidationError(f"Color '{color}' is not available for this product.")
                    
                    ShoeVariant.objects.create(product=instance, **variant_data)

            # Update images if provided
            if images_data is not None:
                if len(images_data) > 3:
                    raise ValidationError("Maximum 3 images allowed per product.")
                
                instance.images.clear()
                for image_data in images_data:
                    image = ProductImage.objects.create(**image_data)
                    instance.images.add(image)

            return instance

        except Exception as e:
            # If anything fails, the transaction will rollback
            raise ValidationError(str(e))

class ClothingVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClothingVariant
        fields = ['id', 'size', 'stock']

    def validate_stock(self, value):
        if value < 0:
            raise ValidationError("Stock cannot be negative")
        return value

class ClothingProductSerializer(BaseProductSerializer):
    variants = ClothingVariantSerializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        model = ClothingProduct
        fields = BaseProductSerializer.Meta.fields + [
            'material', 'color', 'variants'
        ]

    def validate(self, data):
        data = super().validate(data)
        category = data.get('category')
        root_name = category.get_root().name.lower()
        
        if category and root_name != "clothing":
            raise ValidationError(
                {"category": f"Clothing products must belong to the Clothing category. Got '{root_name}' instead."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        images_data = validated_data.pop('images', [])

        # Create the product
        product = ClothingProduct.objects.create(**validated_data)

        # Create variants
        ClothingVariant.objects.bulk_create([
            ClothingVariant(product=product, **variant_data)
            for variant_data in variants_data
        ])

        # Handle images
        if images_data:
            if len(images_data) > 3:
                raise ValidationError({"images": "Maximum 3 images allowed per product."})
            
            for image_data in images_data:
                image = ProductImage.objects.create(**image_data)
                product.images.add(image)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants', None)
        images_data = validated_data.pop('images', None)

        # Update main product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update variants if provided
        if variants_data is not None:
            instance.variants.all().delete()
            ClothingVariant.objects.bulk_create([
                ClothingVariant(product=instance, **variant_data)
                for variant_data in variants_data
            ])

        # Update images if provided
        if images_data is not None:
            if len(images_data) > 3:
                raise ValidationError({"images": "Maximum 3 images allowed per product."})
                
            instance.images.clear()
            for image_data in images_data:
                image = ProductImage.objects.create(**image_data)
                instance.images.add(image)

        return instance