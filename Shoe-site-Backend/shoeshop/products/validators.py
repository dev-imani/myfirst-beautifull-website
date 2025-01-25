from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

def validate_sku(value):
    """
    Validate SKU format.
    
    Args:
        value (str): SKU to validate
    
    Raises:
        ValidationError: If SKU does not meet requirements
    """
    sku_pattern = r'^[A-Z]{3}-\d{4}-[A-Z]{2}$'
    if not re.match(sku_pattern, value):
        raise ValidationError(
            _('SKU must be in format: XXX-1234-YY'),
            params={'value': value}
        )

def validate_positive_price(value):
    """
    Ensure price is positive.
    
    Args:
        value (decimal): Price to validate
    
    Raises:
        ValidationError: If price is not positive
    """
    if value <= 0:
        raise ValidationError(
            _('Price must be a positive number'),
            params={'value': value}
        )

def validate_stock_quantity(value):
    """
    Ensure stock quantity is non-negative.
    
    Args:
        value (int): Stock quantity to validate
    
    Raises:
        ValidationError: If quantity is negative
    """
    if value < 0:
        raise ValidationError(
            _('Stock quantity cannot be negative'),
            params={'value': value}
        )