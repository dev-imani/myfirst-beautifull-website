# users/validators.py
# users/validators.py
from django.core.exceptions import ValidationError
import re
from datetime import datetime
from django.utils.translation import gettext_lazy as _

class CustomUserValidator:
    """
    Validator class for the CustomUser model in the shoe shop system.
    
    Methods:
    - validate_sex: Ensures sex field matches allowed choices
    - validate_username: Checks username format and uniqueness
    - validate_phone_number: Validates phone number format
    - validate_email: Ensures email follows required format
    - validate_name: Validates first and last name format
    - validate_roles: Ensures role assignments are valid
    """
    
    @staticmethod
    def validate_sex(sex):
        """
        Validates the sex field value.
        
        Args:
            sex (str): The sex value to validate
            
        Raises:
            ValidationError: If sex value is invalid
        """
        from users.choices import SexChoices
        
        if not sex:
            raise ValidationError(_("Sex field cannot be empty."))
            
        if sex not in SexChoices.values:
            raise ValidationError(
                _(f"Invalid value for sex: '{sex}'. Must be one of {SexChoices.values}."),
                code="invalid_sex_choice"
            )

    @staticmethod
    def validate_username(username):
        """
        Validates username format and uniqueness.
        
        Args:
            username (str): The username to validate
            
        Raises:
            ValidationError: If username is invalid or duplicate
        """
        from users.models import CustomUser
        
        if not username:
            raise ValidationError(_("Username cannot be empty."))
            
        # Check length
        if len(username) < 3:
            raise ValidationError(
                _("Username must be at least 3 characters long."),
                code="username_too_short"
            )
            
        if len(username) > 45:
            raise ValidationError(
                _("Username cannot exceed 45 characters."),
                code="username_too_long"
            )
            
        # Check format
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(
                _("Username can only contain letters, numbers, and underscores."),
                code="invalid_username_format"
            )
            
        # Check uniqueness
        if (CustomUser.objects.filter(username=username)
                .exclude(username=username)
                .exists()):
            raise ValidationError(
                _("Username already exists."),
                code="duplicate_username"
            )

    @staticmethod
    def validate_phone_number(phone_number):
        """
        Validates phone number format.
        
        Args:
            phone_number (str): The phone number to validate
            
        Raises:
            ValidationError: If phone number format is invalid
        """
        if not phone_number:
            raise ValidationError(_("Phone number cannot be empty."))
            
        # Basic format check (can be expanded based on requirements)
        if not re.match(r'^\+?1?\d{9,15}$', str(phone_number)):
            raise ValidationError(
                _("Invalid phone number format. Must be between 9 and 15 digits."),
                code="invalid_phone_format"
            )

    @staticmethod
    def validate_email(email):
        """
        Validates email format.
        
        Args:
            email (str): The email to validate
            
        Raises:
            ValidationError: If email format is invalid
        """
        if not email:
            raise ValidationError(_("Email cannot be empty."))
            
        # Check format using regex
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError(
                _("Invalid email format."),
                code="invalid_email_format"
            )

    @staticmethod
    def validate_name(name, field_name="name"):
        """
        Validates first and last name format.
        
        Args:
            name (str): The name to validate
            field_name (str): Field name for error messages
            
        Raises:
            ValidationError: If name format is invalid
        """
        if not name:
            raise ValidationError(_(f"{field_name.title()} cannot be empty."))
            
        if len(name) > 20:
            raise ValidationError(
                _(f"{field_name.title()} cannot exceed 20 characters."),
                code=f"{field_name}_too_long"
            )
            
        if not re.match(r'^[a-zA-Z\s\'-]+$', name):
            raise ValidationError(
                _(f"{field_name.title()} can only contain letters, spaces, hyphens, and apostrophes."),
                code=f"invalid_{field_name}_format"
            )

    @staticmethod
    def validate_roles(user):
        """
        Validates user role assignments.
        
        Args:
            user: The user instance to validate
            
        Raises:
            ValidationError: If role assignments are invalid
        """
        # Count active roles
        active_roles = sum([
            user.is_store_owner,
            user.is_store_manager,
            user.is_inventory_manager,
            user.is_sales_associate,
            user.is_customer_service,
            user.is_cashier
        ])
        
        # Check for multiple roles
        if active_roles > 1:
            raise ValidationError(
                _("A user can only have one active role at a time."),
                code="multiple_roles"
            )