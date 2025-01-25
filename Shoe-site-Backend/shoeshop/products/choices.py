from django.db import models

class ProductSizeChoices(models.TextChoices):
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
    ARCHIVED = 'archived', 'Archived'