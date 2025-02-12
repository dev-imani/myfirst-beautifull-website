from datetime import timezone
import hashlib
from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from rest_framework.exceptions import ValidationError
from products.utils import assign_category_order
from products.validators import validate_base_product_status, validate_category_status, validate_name, validate_product_gender, validate_top_level_category, validate_description
from products.choices import CategoryChoices, CategoryStatusChoices, BaseProductStatusChoices, ProductGenderChoices




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

    name = models.CharField(max_length=15, unique=True, blank=True, validators=[validate_name])
    slug = models.SlugField(max_length=20, unique=True, blank=True)
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
        validate_category_status(self.status)
        # Validate unique top-level category
        if self.top_level_category:
            validate_top_level_category(self.top_level_category)
            self.name = dict(CategoryChoices.choices)[self.top_level_category]
            
       
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
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def gt_ancestors(self):
        """
        Return a formatted string of the category's ancestors (parents).
        """
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.insert(0, parent.name)  # Add to the front to maintain order
            parent = parent.parent # pylint: disable=no-member
        return " > ".join(ancestors) if ancestors else None

    def gt_children(self):
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
        indexes = [
            models.Index(fields=['name']),  # Index for searching/filtering by name
            models.Index(fields=['parent']), # Important for MPTT queries and retrieving children
            models.Index(fields=['status']), # useful for filtering by status
            models.Index(fields=['order']),  # Crucial for ordering queries
        ]


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
# models.py

class Brand(models.Model):
    """Represents a product brand.
        name (CharField): The name of the brand, must be unique and have a maximum length of 100 characters.
        description (TextField): A brief description of the brand, can be left blank.
        created_at (DateTimeField): The date and time when the brand was created, automatically set on creation.
        updated_at (DateTimeField): The date and time when the brand was last updated, automatically set on update.
        name_sort (CharField): A case-insensitive version of the brand name used for sorting, not editable by users.
        popularity (PositiveIntegerField): A measure of the brand's popularity, defaults to 0.
    Methods:
        __str__: Returns the string representation of the brand, which is its name.
        clean: Validates the name and description fields.
        save: Sets the name_sort field to a lowercase version of the name before saving the instance.
    Meta:
        ordering (list): Default ordering for the model instances, orders by 'name_sort' in a case-insensitive alphabetical order.
        indexes (list): List of database indexes to be created for the model, includes indexes on 'created_at' and 'name_sort' fields.
    """

    name = models.CharField(max_length=15, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name_sort = models.CharField(max_length=15, editable=False, blank=True)
    popularity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.name)

    def clean(self):
        validate_name(self.name)
        validate_description(self.description)

   
    def save(self, *args, **kwargs):
        self.name_sort = self.name.lower() if self.name else '' # pylint: disable=no-member
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        """
        Meta options for the Product model.

        Attributes:
            verbose_name (str): Human-readable name for the model in singular form.
            verbose_name_plural (str): Human-readable name for the model in plural form.
            ordering (list): Default ordering for the model instances, in this case, 
                             it orders by 'name_sort' in a case-insensitive alphabetical order.
            indexes (list): List of database indexes to be created for the model. 
                            It includes indexes on 'created_at' and 'name_sort' fields.
        """
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['name_sort']  # Case-insensitive alphabetical order
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['name_sort']),
        ]

class ProductImage(models.Model):  # Separate model for product images
    """
    Model representing an image associated with a product.

    Attributes:
        image (ImageField): The image file associated with the product. The file is uploaded to the 'product_images/' directory.
        alt_text (CharField): Optional alternative text for the image, with a maximum length of 50 characters. This can be used for accessibility or SEO purposes.

    Methods:
        __str__(): Returns the name of the image file.
    """
    image = models.ImageField(upload_to='product_images/')  # Adjust upload path as needed
    # You can add other fields related to the image if needed, e.g., alt text
    alt_text = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.image.name
class BaseProduct(models.Model):
    """
    BaseProduct is an abstract base model that defines common attributes and methods for product models.
    Attributes:
        name (CharField): The name of the product, must be unique.
        description (TextField): A brief description of the product, can be blank or null.
        price (DecimalField): The price of the product with up to 10 digits and 2 decimal places.
        brand (ForeignKey): A foreign key to the Brand model, with a protective delete behavior.
        category (TreeForeignKey): A foreign key to the Category model, with a protective delete behavior.
        sku (CharField): A unique stock keeping unit, auto-generated if not provided.
        status (CharField): The status of the product, with choices defined in BaseProductStatusChoices.
        stock (PositiveIntegerField): The available stock quantity of the product.
        created_at (DateTimeField): The timestamp when the product was created, auto-generated.
        updated_at (DateTimeField): The timestamp when the product was last updated, auto-generated.
        images (ManyToManyField): A many-to-many relationship to the ProductImage model, can be blank.
    Methods:
        generate_sku(): Generates a unique SKU using a hash and timestamp.
        clean(): Validates the product attributes and generates SKU if not provided.
        save(*args, **kwargs): Cleans the product and saves it to the database.
        __str__(): Returns the string representation of the product name.
    """
  
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="%(class)s_products")
    category = TreeForeignKey(Category, on_delete=models.PROTECT, related_name="%(class)s_products")
    sku = models.CharField(max_length=100, unique=True, editable=False, blank=True)
    status = models.CharField(max_length=10, choices=BaseProductStatusChoices.choices, default="active")
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    images = models.ManyToManyField(ProductImage, related_name="%(class)s_products" , blank=True) # Many-to-many to images

    class Meta:
        """
        Meta options for the model.

        Attributes:
            abstract (bool): Indicates that this is an abstract base class.
            ordering (list): Specifies the default ordering for the model's objects, 
                             in this case, by the 'created_at' field in descending order.
        """
        abstract = True
        ordering = ["-created_at"]

    def generate_sku(self):
        """
        Generates a unique SKU (Stock Keeping Unit) for a product.

        The SKU is generated by combining the product's brand name, category name,
        product name, and a timestamp. This combined string is then hashed using
        the MD5 algorithm, and the first 15 characters of the hash (in uppercase)
        are returned as the SKU.

        Returns:
            str: A unique SKU for the product.
        """


        timestamp = timezone.now().timestamp() # can use UUID: str(uuid.uuid4()).replace('-', '') if needed for absolute uniqueness

        sku_string = f"{self.brand.name or 'BRD'}{self.category.name or 'CAT'}{self.name}{timestamp}" # Combine attributes and timestamp
        hashed_sku = hashlib.md5(sku_string.encode()).hexdigest()[:15].upper()  # Hash and take first 15 characters

        return hashed_sku

    def clean(self):
        validate_name(self.name)
        validate_description(self.description)
        validate_base_product_status(self.status)
        if not self.sku:
            self.sku = self.generate_sku()
        if not self.category.parent: # pylint: disable=no-member
            raise ValidationError({"category": "Products cannot be assigned to top-level categories."})
        if self.images.count() > 3: # pylint: disable=no-member
            raise ValidationError({"images": "Maximum 3 images allowed per product."})
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

class ShoeProduct(BaseProduct):

    SIZE_TYPES = [
        ("US", "US"),
        ("UK", "UK"),
        ("EU", "EU"),
    ]

    gender = models.CharField(max_length=10, choices=ProductGenderChoices.choices)
    size_type = models.CharField(max_length=5, choices=SIZE_TYPES)
    material = models.CharField(max_length=100)
    style = models.CharField(max_length=100)

    def clean(self):
        super().clean()
        validate_product_gender(self.gender)

        root_category = self.category.get_root()  # Get the root node (MPTT)
        if not root_category.is_root_node() or root_category.name.lower() != "shoes": # Check if it is a root node and the name is correct
            raise ValidationError({"category": _("Shoe products must belong to the Shoes category.")})
        
class ShoeSize(models.Model): # New model for sizes
    product = models.ForeignKey(ShoeProduct, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=10)

    class Meta:
        unique_together = ("product", "size")
        ordering = ["size"]

    def __str__(self):
        return str(self.size)

class ShoeColor(models.Model): # New model for colors
    product = models.ForeignKey(ShoeProduct, on_delete=models.CASCADE, related_name="colors")
    color = models.CharField(max_length=50)


    class Meta:
        unique_together = ("product", "color")
        ordering = ["color"]

    def __str__(self):
        return self.color


class ShoeVariant(models.Model):
    product = models.ForeignKey(ShoeProduct, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=10)  # Size name directly
    color = models.CharField(max_length=50)  # Color name directly
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "size", "color")  # enforce uniqueness
        ordering = ["size", "color"]

    def clean(self):
        if self.stock < 0:
            raise ValidationError({"stock": _("Stock cannot be negative.")})
       

    def __str__(self):
        return f"{self.product.name} - Size {self.size} - Color {self.color}"

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class ClothingProduct(BaseProduct):
    SIZE_CHOICES = [
        ("XS", "Extra Small"),
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
    ]
    material = models.CharField(max_length=100)
    color = models.CharField(max_length=50)

    def clean(self):
        super().clean()
        if not self.category.name.lower() == "clothing":
            raise ValidationError({"category": _("Clothing products must belong to the Clothing category.")})

class ClothingVariant(models.Model):
    """Represents a size variation of a clothing product."""
    product = models.ForeignKey(ClothingProduct, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=5, choices=ClothingProduct.SIZE_CHOICES)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "size")

    def clean(self):
        if self.stock < 0:
            raise ValidationError({"stock": _("Stock cannot be negative.")})

    def __str__(self):
        return f"{self.product.name} - Size {self.size}"


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