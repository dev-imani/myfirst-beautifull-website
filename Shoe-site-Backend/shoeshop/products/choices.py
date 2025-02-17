from django.db import models
class CategoryChoices(models.TextChoices):
    """Enumeration of standard product categories."""
    SHOES = 'shoes', 'Shoes'
    CLOTHING = 'clothing', 'Clothing'
    """ACCESSORIES = 'accessories', 'Accessories'
    ELECTRONICS = 'electronics', 'Electronics'
    HOME = 'home', 'Home'
    TOYS = 'toys', 'Toys'
    BEAUTY = 'beauty', 'Beauty'
    FOOD = 'food', 'Food'
    BOOKS = 'books', 'Books'
    SPORTS = 'sports', 'Sports'
    OUTDOORS = 'outdoors', 'Outdoors'
    AUTOMOTIVE = 'automotive', 'Automotive'
    MUSIC = 'music', 'Music'
    GAMES = 'games', 'Games'
    ART = 'art', 'Art'
    COLLECTIBLES = 'collectibles', 'Collectibles'
    OTHER = 'other', 'Other' """

class CategoryStatusChoices(models.TextChoices):
    """Category availability status."""
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'active'
    INACTIVE = 'inactive', 'inactive'
    ARCHIVED = 'archived', 'Archived'

class BaseProductStatusChoices(models.TextChoices):
    """Base product availability status."""
    ACTIVE = 'active', 'active'
    INACTIVE = 'inactive', 'inactive'
    ARCHIVED = 'archived', 'Archived'

class ProductTypeChoices(models.TextChoices):
    SHOES = 'shoes', 'Shoes'
    CLOTHING = 'clothing', 'Clothing'
class ProductGenderChoices(models.TextChoices):
    """gender choices for  product."""
    MENS = 'mens', 'Mens'
    WOMENS = 'womens', 'Womens'
    UNISEX = 'unisex', 'Unisex'
    
'''class ProductSizeChoices(models.TextChoices):
    """Enumeration of standard shoe sizes."""
    US_5 = '5', 'US 5'
    US_6 = '6', 'US 6'
    US_7 = '7', 'US 7'
    US_8 = '8', 'US 8'
    US_9 = '9', 'US 9'
    US_10 = '10', 'US 10'
    US_11 = '11', 'US 11'
    US_12 = '12', 'US 12'
    US_13 = '13', 'US 13'
    US_14 = '14', 'US 14'

class ProductColorChoices(models.TextChoices):
    """Standard product color choices."""
    BLACK = 'black', 'Black'
    WHITE = 'white', 'White'
    RED = 'red', 'Red'
    BLUE = 'blue', 'Blue'

class ProductStatusChoices(models.TextChoices):
    """Product availability status."""
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    ARCHIVED = 'archived', 'Archived'''