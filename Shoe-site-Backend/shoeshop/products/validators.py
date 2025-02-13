from rest_framework.exceptions import ValidationError
import re
from products.choices import BaseProductStatusChoices, CategoryChoices, CategoryStatusChoices, ProductGenderChoices



def validate_top_level_category(value):
    """
    Validator for top_level_category to ensure it's one of the defined choices.
    """
    if value not in CategoryChoices.values:
        raise ValidationError(
            f"Invalid top_level_category '{value}'. Available choices are: {', '.join([choice[1] for choice in CategoryChoices.choices])}."
        )

def validate_category_status(value):
    """
    Validator for category status to ensure it's one of the defined choices.
    """
    if value not in CategoryStatusChoices.values:
        raise ValidationError(
            f"Invalid category status '{value}'. Available choices are: {', '.join(CategoryStatusChoices.values)}."
        )
    
def validate_base_product_status(value):
    """
    Validator for base product status to ensure it's one of the defined choices.
    """
    if value not in BaseProductStatusChoices.values:
        raise ValidationError(
            f"Invalid base product status '{value}'. Available choices are: {', '.join(BaseProductStatusChoices.values)}."
        )
    
def validate_product_gender(value):
    """Validate product gender"""
    if value not in ProductGenderChoices.values:
        raise ValidationError(
            f"Invalid product gender choice '{value}'. Available choices are: {', '.join(ProductGenderChoices.values)}."
        )


def validate_name(name):
    """
    Validates the name of a product.

    This method checks if the name contains only letters, numbers, spaces, and hyphens.
    It also ensures that the name is at least 3 characters long.

    Raises:
        ValidationError: If the name contains invalid characters or is too short.
    """
    if not re.match(r"^[A-Za-z0-9 \-'&]+$", name):  # Include ', -, &, and space
        raise ValidationError(
            "Name can only contain letters, numbers, spaces, hyphens, apostrophes, and ampersands."
        )
    if len(name) < 3:
        raise ValidationError("Name must be at least 3 characters long.")

def validate_description(description):
    """
    Validates the description of a product.

    This method checks if the description contains any forbidden words 
    such as "fake" or "counterfeit". It also ensures that the description 
    does not exceed 500 characters in length.

    Raises:
        ValidationError: If the description contains forbidden words or 
                         exceeds 500 characters.
    """
    forbidden_words = ["fake", "counterfeit"]
    if any(word in description.lower() for word in forbidden_words):
        raise ValidationError("Description contains forbidden words.")
    if len(description) > 100:
        raise ValidationError("Description is too long, should be less than 500 characters.")
