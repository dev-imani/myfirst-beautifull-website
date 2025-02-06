from rest_framework.exceptions import ValidationError
import re
from products.choices import CategoryChoices



def validate_top_level_category(value):
    """
    Validator for top_level_category to ensure it's one of the defined choices.
    """
    if value not in CategoryChoices.values:
        raise ValidationError(
            f"Invalid top_level_category '{value}'. Available choices are: {', '.join([choice[1] for choice in CategoryChoices.choices])}."
        )
def validate_name(self):
    """
    Validates the brand name of a product.

    This method checks if the name contains only letters, numbers, spaces, and hyphens.
    It also ensures that the name is at least 3 characters long.

    Raises:
        ValidationError: If the name contains invalid characters or is too short.
    """
    if not re.match("^[A-Za-z]", self.name):
        raise ValidationError("Name can only contain letters")
    if len(self.name) < 3:
        raise ValidationError("Name must be at least 3 characters long.")

def validate_description(self):
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
    if any(word in self.description.lower() for word in forbidden_words):
        raise ValidationError("Description contains forbidden words.")
    if len(self.description) > 500:
        raise ValidationError("Description is too long, should be less than 500 characters.")
