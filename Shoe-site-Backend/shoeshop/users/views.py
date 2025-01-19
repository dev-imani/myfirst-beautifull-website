from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import CustomUser
from users.permissions import (
    IsStoreOwner,
    IsStoreManager,
    IsSelfProfile,
    IsInventoryManager,
)
from users.serializers import CustomUserSerializer,CustomUserUpdateSerializer, CustomUserCreateSerializer


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet to handle operations related to custom user accounts.

    Provides CRUD functionality for user accounts.

    Actions:
    - list: Get a list of all custom users excluding the current user.
    - retrieve: Retrieve details of a specific custom user.
    - create: Create a new custom user account.
    - update: Update an existing custom user account.
    - destroy: Delete an existing custom user account.
    - assign_store_owner: Assign the store owner role to selected users.
    - assign_store_manager: Assign the store manager role to selected users.
    - assign_assistant_store_manager: Assign the assistant store manager role to selected users.
    - assign_store_worker: Assign the store worker role to selected users.
    - assign_team_leader_manager: Assign the team leader role to selected users.
    - dismiss_assistant_store_manager: Dismiss the assistant store manager role from selected users.
    - dismiss_store_manager: Dismiss the store manager role from selected users.
    - dismiss_store_worker: Dismiss the store worker role from selected users.
    - dismiss_team_leader_manager: Dismiss the team leader role from selected users.

    Serializer class used for request/response data depends on the action:
    - CustomUserCreateSerializer for the 'create' action.
    - CustomUserSerializer for other actions.
    """

    def get_queryset(self):
        """
        Get the queryset for the view.
        Exclude the current user from the list if the action is 'list'.
        """
        queryset = CustomUser.objects.all()

        if self.action == "list":
            # Exclude the current user from the list
            queryset = queryset.exclude(id=self.request.user.id)
        return queryset

    def get_serializer_class(self):
        """
        Get the serializer class based on the action.
        Use CustomUserCreateSerializer for the 'create' action, and CustomUserSerializer for other actions.
        """
        if self.action == "create":
            return CustomUserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return CustomUserUpdateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        """
        Get the permissions based on the action.

        - For 'list', 'retrieve', 'destroy': Only store owners or store managers are allowed.
        - For 'update': Only the owner of the profile is allowed.
        - For 'assign_store_owner', 'assign_store_manager', 'assign_assistant_store_manager': Only store owners are allowed.
        - For 'assign_store_worker': Only store managers or owners are allowed.
        - For 'assign_team_leader': Only store managers, owners, or assistant store managers are allowed.
        - For 'dismiss_store_manager', 'dismiss_assistant_store_manager': Only store owners are allowed.
        - For 'dismiss_team_leader': store owners, managers, and assistant store managers are allowed.
        - For 'dismiss_store_worker': Only store managers or owners are allowed.

        """
        if self.action in ["list", "retrieve", "destroy"]:
            permission_classes = [IsStoreOwner| IsStoreManager]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsSelfProfile]
        elif self.action in [
            "assign_store_owner",
            "assign_store_manager",
            "assign_assistant_store_manager",
        ]:
            permission_classes = [IsStoreOwner]
        elif self.action == "assign_store_worker":
            permission_classes = [IsStoreManager | IsStoreOwner]
        elif self.action == "assign_team_leader":
            permission_classes = [IsStoreManager | IsStoreOwner | IsAssistantstoreManager]
        elif self.action in ["dismiss_store_manager", "dismiss_assistant_store_manager"]:
            permission_classes = [IsStoreOwner]
        elif self.action == "dismiss_team_leader":
            permission_classes = [IsStoreManager | IsStoreOwner | IsAssistantstoreManager]
        else:
            permission_classes = [IsStoreManager | IsStoreOwner]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def assign_store_owner(self, request):
        """
        Assign store owner roles to selected users.
        The first user in the system automatically becomes a store owner.
        Subsequent store owners can only be assigned by existing store owners.
        
        Request body:
            user_ids: List of user IDs to assign store owner role
            
        Returns:
            Response with success/error messages and appropriate HTTP status code
        """
        # Check if this is the first user
        total_users = CustomUser.objects.count()
        if total_users == 1 and request.user.id == CustomUser.objects.first().id:
            request.user.is_store_owner = True
            request.user.save()
            return Response(
                {"message": "You have been assigned as the first store owner."},
                status=status.HTTP_200_OK
            )

        # For subsequent assignments, verify store owner permission
        if not request.user.is_store_owner:
            return Response(
                {"error": "Only store owners can assign store owner roles."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get and validate user IDs
        user_ids = request.data.getlist("user_ids", [])
        if not user_ids:
            return Response(
                {"error": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_user_id = request.user.id
        assigned_users = []
        not_found_ids = []
        invalid_ids = []
        response_data = {}

        # Process each user ID
        for user_id in user_ids:
            try:
                user_id_int = int(user_id)
                
                # Prevent self-assignment for non-first users
                if user_id_int == current_user_id:
                    return Response(
                        {"error": "Cannot assign store owner role to yourself."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user = CustomUser.objects.get(id=user_id_int)
                
                # Check if user is already a store owner
                if user.is_store_owner:
                    return Response(
                        {"error": f"User {user.username} is already a store owner."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Assign store owner role
                user.assign_store_owner()
                assigned_users.append(user.username)
                
            except ValueError:
                invalid_ids.append(user_id)
            except CustomUser.DoesNotExist:
                if user_id.isdigit():
                    not_found_ids.append(user_id)
                else:
                    invalid_ids.append(user_id)

        # Build response messages
        if assigned_users:
            response_data["message"] = (
                f"Users {', '.join(assigned_users)} have been assigned as store owners."
                if len(assigned_users) > 1
                else f"User {assigned_users[0]} has been assigned as a store owner."
            )

        if not_found_ids:
            response_data["not_found"] = (
                f"Users with IDs {', '.join(not_found_ids)} were not found."
                if len(not_found_ids) > 1
                else f"User with ID {not_found_ids[0]} was not found."
            )

        if invalid_ids:
            response_data["invalid"] = (
                f"Invalid IDs: {', '.join(invalid_ids)}."
                if len(invalid_ids) > 1
                else f"Invalid ID: {invalid_ids[0]}."
            )

        # Return 400 if no users were assigned and there were errors
        if not assigned_users and (not_found_ids or invalid_ids):
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"])
    def assign_store_manager(self, request):
        """
        Assign store manager roles to selected users.
        Store managers can only be assigned by existing store owners.
        
        Request body:
            user_ids: List of user IDs to assign store owner role
            
        Returns:
            Response with success/error messages and appropriate HTTP status code
        """

        # Get and validate user IDs
        user_ids = request.data.getlist("user_ids", [])
        if not user_ids:
            return Response(
                {"error": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_user_id = request.user.id
        assigned_users = []
        not_found_ids = []
        invalid_ids = []
        response_data = {}

        # Process each user ID
        for user_id in user_ids:
            try:
                user_id_int = int(user_id)
                
                # Prevent self-assignment for non-first users
                if user_id_int == current_user_id:
                    return Response(
                        {"error": "Cannot assign store owner role to yourself."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user = CustomUser.objects.get(id=user_id_int)
                
                # Check if user is already a store owner
                if user.is_store_manager:
                    return Response(
                        {"error": f"User {user.username} is already a store owner."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Assign store owner role
                user.assign_store_manager()
                assigned_users.append(user.username)
                
            except ValueError:
                invalid_ids.append(user_id)
            except CustomUser.DoesNotExist:
                if user_id.isdigit():
                    not_found_ids.append(user_id)
                else:
                    invalid_ids.append(user_id)

        # Build response messages
        if assigned_users:
            response_data["message"] = (
                f"Users {', '.join(assigned_users)} have been assigned as store manager."
                if len(assigned_users) > 1
                else f"User {assigned_users[0]} has been assigned as a store manager."
            )

        if not_found_ids:
            response_data["not_found"] = (
                f"Users with IDs {', '.join(not_found_ids)} were not found."
                if len(not_found_ids) > 1
                else f"User with ID {not_found_ids[0]} was not found."
            )

        if invalid_ids:
            response_data["invalid"] = (
                f"Invalid IDs: {', '.join(invalid_ids)}."
                if len(invalid_ids) > 1
                else f"Invalid ID: {invalid_ids[0]}."
            )

        # Return 400 if no users were assigned and there were errors
        if not assigned_users and (not_found_ids or invalid_ids):
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)