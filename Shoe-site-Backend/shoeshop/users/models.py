
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from users.choices import SexChoices, UserRoles

from users.validators import CustomUserValidator

class CustomUser(AbstractUser):
    """
    Custom user model representing a user in the shoe shop system.
    
    Fields:
    - username: Unique identifier for the user (max 45 chars)
    - email: Unique email address (max 50 chars)
    - first_name: User's first name (max 20 chars)
    - last_name: User's last name (max 20 chars)
    - phone_number: Unique phone number (max 15 chars)
    - sex: User's gender (choices from SexChoices)
    - Role boolean fields for different positions
    """
    username = models.CharField(max_length=45, unique=True)
    email = models.EmailField(max_length=50, unique=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    phone_number = PhoneNumberField(max_length=15, unique=True, null=True)
    sex = models.CharField(choices=SexChoices.choices, max_length=6)
    
    # Role fields
    is_store_owner = models.BooleanField(default=False)
    is_store_manager = models.BooleanField(default=False)
    is_inventory_manager = models.BooleanField(default=False)
    is_sales_associate = models.BooleanField(default=False)
    is_customer_service = models.BooleanField(default=False)
    is_cashier = models.BooleanField(default=False)

    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "phone_number",
        "sex",
        "username"
    ]
    USERNAME_FIELD = "email"

    def assign_store_owner(self):
        """Assign store owner role and remove other roles."""
        self._clear_all_roles()
        self.is_store_owner = True
        self.save()

    def assign_store_manager(self):
        """Assign store manager role and remove other roles."""
        self._clear_all_roles()
        self.is_store_manager = True
        self.save()

    def assign_inventory_manager(self):
        """Assign inventory manager role and remove other roles."""
        self._clear_all_roles()
        self.is_inventory_manager = True
        self.save()

    def assign_sales_associate(self):
        """Assign sales associate role and remove other roles."""
        self._clear_all_roles()
        self.is_sales_associate = True
        self.save()

    def assign_customer_service(self):
        """Assign customer service role and remove other roles."""
        self._clear_all_roles()
        self.is_customer_service = True
        self.save()

    def assign_cashier(self):
        """Assign cashier role and remove other roles."""
        self._clear_all_roles()
        self.is_cashier = True
        self.save()
    def clear_all_roles(self):
        """Remove all roles from the user."""
        self._clear_all_roles()
        self.save()
    def _clear_all_roles(self):
        """Helper method to clear all role assignments."""
        self.is_store_owner = False
        self.is_store_manager = False
        self.is_inventory_manager = False
        self.is_sales_associate = False
        self.is_customer_service = False
        self.is_cashier = False

    def dismiss_role(self):
        """Remove all roles from the user."""
        self._clear_all_roles()
        self.save()

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}"

    def get_role(self):
        """Return the current role of the user."""
        if self.is_store_owner:
            return UserRoles.STORE_OWNER
        elif self.is_store_manager:
            return UserRoles.STORE_MANAGER
        elif self.is_inventory_manager:
            return UserRoles.INVENTORY_MANAGER
        elif self.is_sales_associate:
            return UserRoles.SALES_ASSOCIATE
        elif self.is_customer_service:
            return UserRoles.CUSTOMER_SERVICE
        elif self.is_cashier:
            return UserRoles.CASHIER
        return None

    def clean(self):
        """Validate user data before saving."""
        CustomUserValidator.validate_sex(self.sex)
        CustomUserValidator.validate_username(self.username)
        CustomUserValidator.validate_phone_number(self.phone_number)
        CustomUserValidator.validate_name(self.first_name)
        CustomUserValidator.validate_name(self.last_name)
        CustomUserValidator.validate_roles(self)
        
    def __str__(self):
        return str(f"{self.username} - ({self.email})")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
class StoreOwner(models.Model):
    """Store owners model to store store owners in the system."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="store_owner_entry")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Store Owner: {self.user.username}"

