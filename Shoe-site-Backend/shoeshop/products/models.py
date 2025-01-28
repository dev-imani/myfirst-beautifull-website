from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from rest_framework.exceptions import ValidationError
from products.utils import assign_category_order
from products.validators import validate_category_name, validate_top_level_category
from products.choices import CategoryChoices, CategoryStatusChoices




class Category(MPTTModel):
    """
    Category model to represent hierarchical categories using MPTT (Modified Preorder Tree Traversal).

    Attributes:
        name (str): The name of the category.
        slug (str): A unique slug for the category, auto-generated if not provided.
        description (str): An optional description of the category.
        parent (Category): A self-referential foreign key to define the parent category.
        status (str): The status of the category (e.g., active, inactive, draft).
        order (int): The order of the category for display purposes.
        created_at (datetime): Timestamp when the category was created.
        updated_at (datetime): Timestamp when the category was last updated.
    """

    name = models.CharField(max_length=100, unique=True, validators=[validate_category_name])
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    top_level_category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        null=True,
        blank=True,
        help_text="Required only for top-level categories"
    )
    status = models.CharField(max_length=20, choices=CategoryStatusChoices, default='active')
    order = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate unique top-level category
        if self.top_level_category:
            self.name = dict(CategoryChoices.choices)[self.top_level_category]
            validate_top_level_category(self.top_level_category)
        # Assign slug if not already set
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Category.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        # Assign order if not already set
        if not self.order:
            self.order = assign_category_order(self.parent)

    def save(self, *args, **kwargs):
        # Ensure clean() is always called before save
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_ancestors(self):
        """
        Return a formatted string of the category's ancestors (parents).
        """
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.insert(0, parent.name)  # Add to the front to maintain order
            parent = parent.parent
        return " > ".join(ancestors) if ancestors else None

    def get_children(self):
        """
        Return a formatted string of the category's children.
        """
        children = super().get_children()
        return ", ".join([child.name for child in children])

    def pretty_print(self):
        """
        Return a formatted printout of the category with parents and children.
        """
        ancestors = self.get_ancestors()
        children = self.get_children()

        result = f"Category: {self.name}\n"
        if ancestors:
            result += f"Parents: {ancestors}\n"
        else:
            result += "Parents: None\n"

        result += f"Description: {self.description if self.description else 'No description'}\n"
        result += f"Status: {self.status}\n"
        result += f"Children: {children if children else 'No children'}"
        return result
    
    @classmethod
    def create_top_level_category(cls, category_choice):
        """
        Helper method to create top-level categories
        """
        if category_choice not in CategoryChoices.values:
            raise ValidationError(f"Invalid category choice: {category_choice}")
        
        return cls.objects.create(
            top_level_category=category_choice,
            name=dict(CategoryChoices.choices)[category_choice]
        )

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order']


# Example Usage of MPTT Queries
# Assuming categories are structured as follows:
# - Shoes (id=1)
#   - Men's Shoes (id=2)
#     - Sneakers (id=3)
#
# Queries:
# 1. Get all top-level categories:
#    top_level_categories = Category.objects.filter(parent__isnull=True)
#
# 2. Get all children of a specific category:
#    men_shoes = Category.objects.get(id=2)
#    children = men_shoes.get_children()
#
# 3. Get all descendants of a category (all levels):
#    sneakers_descendants = men_shoes.get_descendants()
#
# 4. Get all ancestors of a category:
#    ancestors = sneakers.get_ancestors()
#
# 5. Get root category of a category:
#    root = sneakers.get_root()





'''from django.db import models
from rest_framework.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone

from products.choices import (
    ProductSizeChoices, 
    ProductColorChoices, 
    ProductStatusChoices
)
from products.validators import (
    validate_sku, 
    validate_positive_price, 
    validate_stock_quantity
)

class Brand(models.Model):
    """Represents a shoe brand."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Represents a shoe product with comprehensive tracking.
    
    Attributes:
        name (str): Product name
        slug (str): URL-friendly identifier
        sku (str): Unique stock keeping unit
        brand (Brand): Associated brand
        description (str): Product description
        price (decimal): Product price
        color (str): Product color
        status (str): Product availability status
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    sku = models.CharField(
        max_length=15, 
        unique=True, 
        validators=[validate_sku]
    )
    brand = models.ForeignKey(
        Brand, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[validate_positive_price]
    )
    color = models.CharField(
        max_length=20, 
        choices=ProductColorChoices.choices
    )
    status = models.CharField(
        max_length=20, 
        choices=ProductStatusChoices.choices,
        default=ProductStatusChoices.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Perform additional model-level validations.
        
        Raises:
            ValidationError: If validation fails
        """
        # Ensure slug is generated from name if not manually set
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Additional custom validations can be added here
        if len(self.description) < 10:
            raise ValidationError({
                'description': 'Description must be at least 10 characters long.'
            })
        
        # Ensure unique SKU across products
        existing_product = Product.objects.filter(sku=self.sku).exclude(pk=self.pk)
        if existing_product.exists():
            raise ValidationError({
                'sku': 'This SKU is already in use.'
            })

    def save(self, *args, **kwargs):
        """
        Override save method for additional processing.
        
        Performs full model validation before saving.
        """
        self.full_clean()  # Runs model validation
        self.updated_at = timezone.now()
        
        # Ensure slug is unique
        original_slug = self.slug
        counter = 1
        while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"

class ProductStock(models.Model):
    """
    Manages stock levels for different product sizes.
    
    Attributes:
        product (Product): Associated product
        size (str): Shoe size
        quantity (int): Available stock quantity
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='stock_sizes'
    )
    size = models.CharField(
        max_length=10, 
        choices=ProductSizeChoices.choices
    )
    quantity = models.IntegerField(
        validators=[validate_stock_quantity],
        default=0
    )

    class Meta:
        unique_together = ['product', 'size']

    def clean(self):
        """
        Validate stock entry before saving.
        """
        # Additional validations can be added here
        pass

    def __str__(self):
        return f"{self.product.name} - Size {self.size}: {self.quantity}"'''