from rest_framework.exceptions import ValidationError
from products.choices import CategoryChoices

def validate_category_name(value):
    """
    Validate category name to prevent reserved or restricted names.
    """
    if len(value) < 3:
        raise ValidationError("Category name must be at least 3 characters long.")
    


def validate_top_level_category(value):
    """
    Validator for top_level_category to ensure it's one of the defined choices.
    """
    if value not in CategoryChoices.values:
        raise ValidationError(
            f"Invalid top_level_category '{value}'. Available choices are: {', '.join([choice[1] for choice in CategoryChoices.choices])}."
        )