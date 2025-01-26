from products.models import Category
from django.db import models

def assign_category_order(parent_category=None):
    """
    Automatically assign a unique order value for categories based on their parent.

    Args:
        parent_category (Category, optional): The parent category object. Defaults to None.

    Returns:
        int: The next available order value for the category.
    """
    try:
        if parent_category:
            # For subcategories
            max_order = Category.objects.filter(parent=parent_category).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            return max_order + 1
        else:
            # For top-level categories
            max_order = Category.objects.filter(parent__isnull=True).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            return max_order + 1
    except Exception:
        return 1  # Fallback to 1 in case of any error

