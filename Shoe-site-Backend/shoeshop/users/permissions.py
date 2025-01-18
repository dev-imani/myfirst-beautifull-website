# users/permissions.py
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.permissions import BasePermission

class IsSelfProfile(BasePermission):
    """
    Custom permission class that allows actions only if the user is the owner of the profile.
    
    Usage:
        Add to views requiring user's own profile access:
        permission_classes = [IsSelfProfile]
    """
    message = {
        "error": "You do not have permission to perform this action on another user's profile."
    }

    def has_object_permission(self, request, view, obj):
        return obj == request.user

class IsStoreOwner(BasePermission):
    """
    Custom permission class that allows only store owners to perform an action.
    
    Usage:
        Add to views requiring store owner access:
        permission_classes = [IsStoreOwner]
    """
    message = {"error": "Only store owners have permission to perform this action."}

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if request.user.is_store_owner:
            return True
        raise PermissionDenied(self.message)

class IsStoreManager(BasePermission):
    """
    Custom permission class that allows store owners and managers to perform an action.
    
    Usage:
        Add to views requiring store management access:
        permission_classes = [IsStoreManager]
    """
    message = {
        "error": "Only store owners and managers have permission to perform this action."
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if request.user.is_store_owner or request.user.is_store_manager:
            return True
        raise PermissionDenied(self.message)

class IsInventoryManager(BasePermission):
    """
    Custom permission class that allows store owners, managers, and inventory managers to perform an action.
    
    Usage:
        Add to views requiring inventory management access:
        permission_classes = [IsInventoryManager]
    """
    message = {
        "error": "Only store owners, managers, and inventory managers have permission to perform this action."
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if (request.user.is_store_owner or 
            request.user.is_store_manager or 
            request.user.is_inventory_manager):
            return True
        raise PermissionDenied(self.message)

class IsSalesAssociate(BasePermission):
    """
    Custom permission class that allows store staff to perform sales-related actions.
    
    Usage:
        Add to views requiring sales staff access:
        permission_classes = [IsSalesAssociate]
    """
    message = {
        "error": "Only sales staff have permission to perform this action."
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if (request.user.is_store_owner or 
            request.user.is_store_manager or 
            request.user.is_sales_associate):
            return True
        raise PermissionDenied(self.message)

class IsCustomerService(BasePermission):
    """
    Custom permission class that allows customer service staff to perform support actions.
    
    Usage:
        Add to views requiring customer service access:
        permission_classes = [IsCustomerService]
    """
    message = {
        "error": "Only customer service staff have permission to perform this action."
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if (request.user.is_store_owner or 
            request.user.is_store_manager or 
            request.user.is_customer_service):
            return True
        raise PermissionDenied(self.message)

class IsCashier(BasePermission):
    """
    Custom permission class that allows cashiers to perform payment-related actions.
    
    Usage:
        Add to views requiring cashier access:
        permission_classes = [IsCashier]
    """
    message = {
        "error": "Only cashiers have permission to perform this action."
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if (request.user.is_store_owner or 
            request.user.is_store_manager or 
            request.user.is_cashier):
            return True
        raise PermissionDenied(self.message)

class IsStoreStaff(BasePermission):
    """
    Custom permission class that allows any store staff member to perform general actions.
    
    Usage:
        Add to views requiring any staff access:
        permission_classes = [IsStoreStaff]
    """
    message = {
        "error": "Only store staff members have permission to perform this action."
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise AuthenticationFailed({
                "error": "Authentication credentials were not provided! Please login to proceed."
            })
        if (request.user.is_store_owner or 
            request.user.is_store_manager or 
            request.user.is_inventory_manager or 
            request.user.is_sales_associate or 
            request.user.is_customer_service or 
            request.user.is_cashier):
            return True
        raise PermissionDenied(self.message)