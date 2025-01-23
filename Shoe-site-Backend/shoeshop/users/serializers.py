# users/serializers.py
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from phonenumber_field.serializerfields import PhoneNumberField
from phonenumbers import parse, PhoneNumberFormat
import phonenumbers
from rest_framework import serializers
User = get_user_model()

class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Custom serializer for creating user instances with additional fields.

    Fields:
    - `phone_number`: A PhoneNumberField for storing standardized phone numbers
    - Additional fields for user roles and basic information

    Usage:
        Use this serializer for new user registration with all required fields.
        Example:
        ```
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password123",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "sex": "MALE"
        }
        ```
    """
    phone_number = PhoneNumberField()

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "sex"
        )

    def create(self, validated_data):
        user = super().create(validated_data)
        # Clear all roles after user creation
        user._clear_all_roles()
        user.save()
        return user
class CustomUserSerializer(UserSerializer):
    """
    Custom serializer for retrieving and updating user instances.

    Fields:
    - `phone_number`: A PhoneNumberField for storing standardized phone numbers
    - All user profile fields and role indicators

    Usage:
        Use this serializer for viewing and updating existing user profiles.
        Example:
        ```
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "sex": "MALE",
            "is_store_owner": false,
            "is_store_manager": true,
            "is_inventory_manager": false,
            "is_sales_associate": false,
            "is_customer_service": false,
            "is_cashier": false
        }
        ```
    """
    phone_number = PhoneNumberField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "sex",
            "is_store_owner",
            "is_store_manager",
            "is_inventory_manager",
            "is_sales_associate",
            "is_customer_service",
            "is_cashier"
        )

class UserProfileSerializer(UserSerializer):
    """
    Simplified serializer for public user profile information.
    Excludes sensitive information and role indicators.

    Usage:
        Use this serializer for public-facing user information.
        Example:
        ```
        {
            "id": 1,
            "username": "john_doe",
            "first_name": "John",
            "last_name": "Doe"
        }
        ```
    """
    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name"
        )
class CustomUserUpdateSerializer(UserSerializer):
    """
    Serializer for updating non-sensitive user information.
    Excludes role modifications and sensitive data changes.

    Fields:
    - Basic profile information only
    - Phone number

    Usage:
        Use this serializer specifically for update operations on user profiles.
        Example:
        ```
        {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890"
        }
        ```
    """
    phone_number = PhoneNumberField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "sex",
            "is_store_owner",
            "is_store_manager",
            "is_inventory_manager",
            "is_sales_associate",
            "is_customer_service",
            "is_cashier"
        )

    def update(self, instance, validated_data):
        # Only update allowed fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance


class StaffMemberSerializer(UserSerializer):
    """
    Serializer for staff member details with comprehensive role information.
    """
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    contact_information = serializers.SerializerMethodField()
    
    class Meta:
        model = User # Use CustomUser 
        fields = [
            'id', 
            'username', 
            'email',
            'full_name', 
            'role',
            'contact_information',
            'date_joined',
            'last_login'
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        """
        Return the user's full name.
        Fallback to username if no full name is available.
        """
        full_name = obj.get_full_name().strip()
        return full_name if full_name else obj.username

    def get_role(self, obj):
        """
        Determine the primary role of the staff member.
        Returns the first role found in order of priority.
        """
        role_priority = [
            ('is_store_owner', 'store_owner'),
            ('is_store_manager', 'store_manager'),
            ('is_inventory_manager', 'inventory_manager'),
            ('is_sales_associate', 'sales_associate'),
            ('is_customer_service', 'customer_service'),
            ('is_cashier', 'cashier')
        ]
        
        for role_field, role_name in role_priority:
            if getattr(obj, role_field, False):
                return role_name
        
        return None

    def get_contact_information(self, obj):
        """
        Provide contact details with robust phone number handling.
        """
        contact_info = {
            'email': obj.email,
            'phone_number': None,
        }
        
        # Directly access PhoneNumberField
        phone_number = obj.phone_number
        
        if phone_number:
            try:
                # Convert to string if needed
                phone_str = str(phone_number)
                
                contact_info['phone_number'] = {
                    'raw': phone_str,
                    'formatted': phone_number.as_international,  # Django phonenumber method
                    'is_valid': phone_number.is_valid()
                }
            except Exception:
                # Fallback if parsing fails
                contact_info['phone_number'] = {
                    'raw': phone_str,
                    'is_valid': False
                }
        
        return {k: v for k, v in contact_info.items() if v is not None}
    def to_representation(self, instance):
        """
        Customize the representation of the serializer.
        Add additional context or computed fields if needed.
        """
        representation = super().to_representation(instance)
        
        # Add any additional computed or context-based fields
        representation['is_active'] = instance.is_active
        
        # Optional: Add profile picture URL if implemented
        if hasattr(instance, 'profile_picture'):
            representation['profile_picture'] = instance.profile_picture.url if instance.profile_picture else None
        
        return representation