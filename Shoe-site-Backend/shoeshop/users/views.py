from rest_framework import status, viewsets, pagination
from django.core.exceptions import FieldError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from users.choices import UserRoles
from users.models import CustomUser, StoreOwner
from users.permissions import (
    IsStoreOwner,
    IsStoreManager,
    IsSelfProfile,
    IsInventoryManager,
)
from rest_framework.permissions import IsAuthenticated
from users.serializers import CustomUserSerializer,CustomUserUpdateSerializer, CustomUserCreateSerializer, StaffMemberSerializer
from users.utils import StaffMemberPagination


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
    - assign_inventory_manager Assign the inventory manager role to selected users.
    - assign_sales_associate: Assign the sales associate role to selected users.
    - assign_customer_service: Assign the customer service role to selected users.
    - assign_cashier: Assign the cashier role to selected users.
   
    
    Serializer class used for request/response data depends on the action:
    - CustomUserCreateSerializer for the 'create' action.
    - CustomUserUpdateSerializer for the 'update' action.
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
        elif self.action in ["update", "partial_update", "put", "patch"]:
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
        # Special case for first store owner assignment
        if self.action == "assign_store_owner" and not StoreOwner.objects.exists():
            return [IsAuthenticated()]
        if self.action in ["list", "retrieve", "destroy"]:
            permission_classes = [IsStoreOwner| IsStoreManager]
        elif self.action in ["update", "partial_update", "put", "patch"]:
            permission_classes = [IsSelfProfile]
        elif self.action in [
            "assign_store_owner",
            "assign_store_manager",
            "dismiss_role"
        ]:
            permission_classes = [IsStoreOwner]
        elif self.action in ["assign_inventory_manager", "get_staff_members", "assign_cashier", "assign_sales_associate", "assign_customer_service", "get_available_staff_roles"]:
            permission_classes = [IsStoreManager]
        else:
            permission_classes = [IsStoreManager | IsStoreOwner]

        return [permission() for permission in permission_classes]

    class RoleAssignmentAndDismissalHandler:
        """
        Utility class for processing role assignments and dismissals within the ViewSet.
        Works with boolean fields on CustomUser model.
        """
        
        def __init__(self, role_type=None):
            self.role_type = role_type
            # Only set these configurations if we're doing an assignment
            if role_type is not None:
                self.role_configs = {
                    'store_owner': {
                        'field': 'is_store_owner',
                        'display_name': 'store owner'
                    },
                    'store_manager': {
                        'field': 'is_store_manager',
                        'display_name': 'store manager'
                    },
                    'inventory_manager': {
                        'field': 'is_inventory_manager',
                        'display_name': 'inventory manager'
                    }, 
                    'customer_service': {
                        'field': 'is_customer_service',
                        'display_name': 'customer service'
                    },
                    'sales_associate': {
                        'field': 'is_sales_associate',
                        'display_name': 'sales associate'
                    }
                }
                if role_type in self.role_configs:
                    self.config = self.role_configs[role_type]
                else:
                    raise ValueError(f"Invalid role type: {role_type}")
                    

        def _build_process_assignment_response__messages(self, assigned_users, not_found_ids, invalid_ids, error_messages):
            """Build response messages for the assignment results."""
            messages = {}
            
            # Handle successful assignments
            if assigned_users:
                messages["message"] = (
                    f"Users {', '.join(assigned_users)} have been assigned as "
                    f"{self.config['display_name']}s."
                    if len(assigned_users) > 1
                    else f"User {assigned_users[0]} has been assigned as a "
                    f"{self.config['display_name']}."
                )
            
            # Handle users not found
            if not_found_ids:
                messages["not_found"] = (
                    f"Users with IDs {', '.join(not_found_ids)} were not found."
                    if len(not_found_ids) > 1
                    else f"User with ID {not_found_ids[0]} was not found."
                )
            
            # Handle invalid IDs
            if invalid_ids:
                messages["invalid"] = (
                    f"Invalid IDs: {', '.join(invalid_ids)}."
                    if len(invalid_ids) > 1
                    else f"Invalid ID: {invalid_ids[0]}."
                )

            # Handle error messages (if any)
            if error_messages:
                messages["errors"] = error_messages  # Include all collected error messages

            return messages
        
        def process_assignments(self, current_user_id, user_ids):
            """Process role assignments for multiple users."""
            assigned_users = []
            not_found_ids = []
            invalid_ids = []
            error_messages = []
            
            # Convert valid IDs to integers and filter out invalid ones
            valid_ids = []
            for user_id in user_ids:
                try:
                    user_id_int = int(user_id)
                    if user_id_int == current_user_id:
                        error_messages.append(f"Cannot assign {self.config['display_name']} role to yourself.")
                        continue
                    valid_ids.append(user_id_int)
                except ValueError:
                    invalid_ids.append(user_id)
            
            if valid_ids:
                # Efficiently fetch existing users
                existing_users = CustomUser.objects.filter(id__in=valid_ids)
                existing_user_ids = {user.id: user for user in existing_users}
                
                # Process each valid ID
                for user_id in valid_ids:
                    user = existing_user_ids.get(user_id)
                    if not user:
                        not_found_ids.append(str(user_id))
                        continue
                    
                    # FULL METHOD TO CLEAR ALL ROLES
                    user._clear_all_roles()
                    
                    # Set the specific role
                    setattr(user, self.config['field'], True)
                    
                    # Save with ALL role fields to ensure consistent update
                    role_fields = [
                        'is_store_owner', 'is_store_manager', 'is_inventory_manager', 
                        'is_sales_associate', 'is_customer_service'
                    ]
                    user.save(update_fields=role_fields)
                    
                    assigned_users.append(user.username)
            
            # Build response messages
            response_data = self._build_process_assignment_response__messages(
                assigned_users, not_found_ids, invalid_ids, error_messages
            )
            
            return {
                'assigned_users': assigned_users,
                'not_found_ids': not_found_ids,
                'invalid_ids': invalid_ids,
                'response_data': response_data
            }

        def process_dismissals(self, current_user_id, user_ids):
            """
            Process role dismissals for multiple users.
            
            Args:
                current_user_id (int): ID of the user initiating the dismissal
                user_ids (list): List of user IDs to dismiss
            
            Returns:
                dict: Comprehensive results of the dismissal process
            """
            # Initialize result tracking containers
            result = {
                'dismissed_users': [],
                'not_found_ids': [],
                'no_roles_ids': [],
                'error_messages': [],
                'response_data': {}
            }
            
            # Validate and prepare user IDs
            valid_ids = self._validate_user_ids(current_user_id, user_ids, result)
            
            # If no valid IDs, return early
            if not valid_ids:
                result['response_data'] = self._build_dismissal_response(result)
                return result
            
            # Fetch existing users efficiently
            existing_users = self._fetch_existing_users(valid_ids)
            
            # Process each valid user
            for user in existing_users:
                try:
                    self._process_user_dismissal(user, result)
                except Exception as e:
                    result['error_messages'].append(
                        f"Error dismissing roles for user {user.username}: {str(e)}"
                    )
            
            # Generate response messages
            result['response_data'] = self._build_dismissal_response(result)
            
            return result

        def _validate_user_ids(self, current_user_id, user_ids, result):
            """
            Validate and filter user IDs.
            
            Args:
                current_user_id (int): ID of the current user
                user_ids (list): List of user IDs to validate
                result (dict): Result tracking dictionary
            
            Returns:
                list: Validated user IDs
            """
            valid_ids = []
            
            for user_id in user_ids:
                try:
                    user_id_int = int(user_id)
                    
                    # Prevent self-dismissal
                    if user_id_int == current_user_id:
                        result['error_messages'].append("You cannot dismiss yourself.")
                        continue
                    
                    valid_ids.append(user_id_int)
                
                except ValueError:
                    result['not_found_ids'].append(user_id)
            
            return valid_ids

        def _fetch_existing_users(self, valid_ids):
            """
            Fetch existing users based on valid IDs.
            
            Args:
                valid_ids (list): List of validated user IDs
            
            Returns:
                QuerySet: Existing users
            """
            return CustomUser.objects.filter(id__in=valid_ids)

        def _process_user_dismissal(self, user, result):
            """
            Process dismissal for a single user.
            
            Args:
                user (CustomUser): User to dismiss
                result (dict): Result tracking dictionary
            """
            # Check if user has a role
            user_role = user.get_role()
            
            if user_role is None:
                result['no_roles_ids'].append(str(user.id))
                return
            
            # Special handling for store owner
            if user_role == UserRoles.STORE_OWNER and hasattr(user, 'store_owner_entry'):
                user.store_owner_entry.delete()
            
            # Clear user roles
            role_field = f'is_{user_role.lower()}'
            
            if hasattr(user, role_field):
                setattr(user, role_field, False)
                user.save(update_fields=[role_field])
                result['dismissed_users'].append(user.username)

        def _build_dismissal_response(self, result):
            """
            Build response messages based on dismissal results.
            
            Args:
                result (dict): Result tracking dictionary
            
            Returns:
                dict: Response messages
            """
            messages = {}
            
            # Dismissed users message
            if result['dismissed_users']:
                messages['message'] = (
                    f"Users {', '.join(result['dismissed_users'])} have been dismissed from their roles."
                    if len(result['dismissed_users']) > 1
                    else f"User {result['dismissed_users'][0]} has been dismissed from their role."
                )
            
            # Not found users message
            if result['not_found_ids']:
                messages['not_found'] = (
                    f"Users with IDs {', '.join(result['not_found_ids'])} were not found."
                    if len(result['not_found_ids']) > 1
                    else f"User with ID {result['not_found_ids'][0]} was not found."
                )
            
            # No roles message
            if result['no_roles_ids']:
                messages['no_roles'] = (
                    f"Users with IDs {', '.join(result['no_roles_ids'])} have no roles to dismiss."
                    if len(result['no_roles_ids']) > 1
                    else f"User with ID {result['no_roles_ids'][0]} has no role to dismiss."
                )
            
            # Error messages
            if result['error_messages']:
                messages['errors'] = result['error_messages']
    
            return messages
        def _format_empty_response(self, response_data):
            """Format response for error cases with no assignments."""
            return {
                'assigned_users': [],
                'not_found_ids': [],
                'invalid_ids': [],
                'response_data': response_data
            }
        
    @action(detail=False, methods=["post"])
    def assign_store_owner(self, request):
        """Assign store owner roles to selected users."""
        # Handle first store owner case
         # Check if this is the first user (ID=1) case
        if not StoreOwner.objects.exists():
            if request.user.id != 1:
                return Response(
                    {"error": "Only the first registered user (ID=1) can become the initial store owner."},
                    status=status.HTTP_403_FORBIDDEN
                )
            StoreOwner.objects.create(user=request.user)
            request.user.is_store_owner = True
            request.user.save()
            return Response(
                {"message": "You have been assigned as the first store owner."},
                status=status.HTTP_200_OK
        )

        # Get and validate user IDs
        user_ids = request.data.getlist("user_ids", [])
        if not user_ids:
            return Response(
                {"error": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process assignments using the universal handler
        handler = self.RoleAssignmentAndDismissalHandler(role_type='store_owner')
        result = handler.process_assignments(request.user.id, user_ids)
        
        if not result['assigned_users'] and (result['not_found_ids'] or result['invalid_ids']):
            return Response(result['response_data'], status=status.HTTP_400_BAD_REQUEST)
        
        # For each user that was assigned the store owner role, create an associated StoreOwner entry
        for username in result['assigned_users']:
            user = CustomUser.objects.get(username=username)
            StoreOwner.objects.create(user=user)  # Associate with StoreOwner model
        return Response(result['response_data'], status=status.HTTP_200_OK)
   
        
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

        # Process assignments using the universal handler
        handler = self.RoleAssignmentAndDismissalHandler(role_type='store_manager')
        result = handler.process_assignments(request.user.id, user_ids)
        
        if not result['assigned_users'] and (result['not_found_ids'] or result['invalid_ids']):
            return Response(result['response_data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['response_data'], status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"])
    def assign_inventory_manager(self, request):
        """
        Assign inventory manager roles to selected users.
        
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

        # Process assignments using the universal handler
        handler = self.RoleAssignmentAndDismissalHandler(role_type='inventory_manager')
        result = handler.process_assignments(request.user.id, user_ids)
        
        if not result['assigned_users'] and (result['not_found_ids'] or result['invalid_ids']):
            return Response(result['response_data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['response_data'], status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"])
    def assign_sales_associate(self, request):
        """
        Assign sales associate roles to selected users.
        
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

        # Process assignments using the universal handler
        handler = self.RoleAssignmentAndDismissalHandler(role_type='sales_associate')
        result = handler.process_assignments(request.user.id, user_ids)
        
        if not result['assigned_users'] and (result['not_found_ids'] or result['invalid_ids']):
            return Response(result['response_data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['response_data'], status=status.HTTP_200_OK)
    

    @action(detail=False, methods=["post"])
    def assign_customer_service(self, request):
        """
        Assign customer service roles to selected users.
        
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

        # Process assignments using the universal handler
        handler = self.RoleAssignmentAndDismissalHandler(role_type='customer_service')
        result = handler.process_assignments(request.user.id, user_ids)
        
        if not result['assigned_users'] and (result['not_found_ids'] or result['invalid_ids']):
            return Response(result['response_data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['response_data'], status=status.HTTP_200_OK)
    

    @action(detail=False, methods=["post"])
    def assign_cashier(self, request):
        """
        Assign customer service roles to selected users.
        
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

        # Process assignments using the universal handler
        handler = self.RoleAssignmentAndDismissalHandler(role_type='cashier')
        result = handler.process_assignments(request.user.id, user_ids)
        
        if not result['assigned_users'] and (result['not_found_ids'] or result['invalid_ids']):
            return Response(result['response_data'], status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result['response_data'], status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='dismiss-role')
    def dismiss_role(self, request):
        """
        Dismiss roles for users (store owner, manager, etc.).

        Request body:
        - user_ids: List of user IDs to be dismissed.

        Returns:
            Response with success/error messages and appropriate HTTP status code
        """
        user_ids = request.data.getlist("user_ids", [])
        current_user_id = request.user.id  # The ID of the user making the request (typically the logged-in user)

        if  not user_ids:
            return Response(
                {"error": "User IDs must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Create the role handler for the specified role
        role_handler = self.RoleAssignmentAndDismissalHandler()

        # Process the dismissals
        result = role_handler.process_dismissals(current_user_id, user_ids)

        # Return the result
        return Response(result, status=status.HTTP_200_OK)
    
class StaffMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing and retrieving staff member information.
    Provides advanced filtering, searching, and ordering capabilities.
    """

    serializer_class = StaffMemberSerializer

    # Predefined role configurations
    ROLE_MAPPING = {
        'store_owner': 'is_store_owner',
        'store_manager': 'is_store_manager',
        'inventory_manager': 'is_inventory_manager',
        'sales_associate': 'is_sales_associate',
        'customer_service': 'is_customer_service'
    }

    def get_queryset(self):
        """
        Custom queryset to only return staff members with roles
        """
        return CustomUser.objects.filter(
            Q(is_store_owner=True) | 
            Q(is_store_manager=True) | 
            Q(is_inventory_manager=True) | 
            Q(is_sales_associate=True) | 
            Q(is_customer_service=True)
        )
    def get_permissions(self):
        if self.action in ["get_staff_members", "get_staff_roles_summary"]:
            permission_classes = [IsStoreManager]
        return [permission() for permission in permission_classes]
    @action(detail=False, methods=['get'], url_path='staff-members')
    def get_staff_members(self, request):
        """
        Retrieve staff members with advanced filtering, searching, and ordering.
        """
        # Construct base query for staff members
        staff_query = self.get_queryset()

        # Apply filters
        staff_query = self._apply_role_filter(staff_query, request)
        staff_query = self._apply_search_filter(staff_query, request)
        staff_query = self._apply_ordering(staff_query, request)

        # Paginate results
        paginator = StaffMemberPagination()
        page = paginator.paginate_queryset(staff_query, request)

        # Serialize data using the StaffMemberSerializer
        serializer = self.get_serializer(page, many=True)

        # Prepare comprehensive response
        response_data = self._prepare_staff_response(
            staff_query, page, serializer.data
        )

        return Response(
            paginator.get_paginated_response(response_data).data, 
            status=status.HTTP_200_OK
        )

    def _apply_role_filter(self, queryset, request):
        """
        Apply role-based filtering to the staff query.
        """
        role_type = request.query_params.get('role_type')
        
        if role_type:
            if role_type not in self.ROLE_MAPPING:
                raise ValidationError({
                    "error": f"Invalid role type. Valid types are: {', '.join(self.ROLE_MAPPING.keys())}"
                })
            
            return queryset.filter(**{self.ROLE_MAPPING[role_type]: True})
        
        return queryset

    def _apply_search_filter(self, queryset, request):
        """
        Apply search filter across multiple user fields.
        """
        search_term = request.query_params.get('search')
        
        if search_term:
            return queryset.filter(
                Q(username__icontains=search_term) | 
                Q(first_name__icontains=search_term) | 
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term)
            )
        
        return queryset

    def _apply_ordering(self, queryset, request):
        """
        Apply custom ordering to the queryset.
        """
        order_by = request.query_params.get('order_by', 'id')
        
        # Support for multiple ordering fields
        ordering_fields = order_by.split(',')
        valid_fields = [
            'id', 'username', 'first_name', 'last_name', 
            'email', 'date_joined'
        ]
        
        try:
            # Validate and apply ordering
            safe_ordering = []
            for field in ordering_fields:
                clean_field = field.strip()
                
                # Handle potential negative (descending) ordering
                if clean_field.startswith('-'):
                    base_field = clean_field[1:]
                    if base_field in valid_fields:
                        safe_ordering.append(clean_field)
                elif clean_field in valid_fields:
                    safe_ordering.append(clean_field)
            
            return queryset.order_by(*safe_ordering) if safe_ordering else queryset
        
        except FieldError:
            # Fallback to default ordering
            return queryset.order_by('id')

    def _prepare_staff_response(self, full_queryset, page_queryset, serialized_data):
        """
        Prepare comprehensive response with metadata.
        """
        return {
            "staff_members": serialized_data,
            "total_count": full_queryset.count(),
            "filtered_count": len(page_queryset) if page_queryset else 0,
            "roles_breakdown": {
                role: full_queryset.filter(**{field: True}).count()
                for role, field in self.ROLE_MAPPING.items()
            }
        }

    @action(detail=False, methods=['get'], url_path='staff-roles')
    def get_staff_roles_summary(self, request):
        """
        Retrieve summary of staff roles and their counts.
        """
        role_counts = {
            role: CustomUser.objects.filter(**{field: True}).count()
            for role, field in self.ROLE_MAPPING.items()
        }

        return Response({
            "total_staff_count": sum(role_counts.values()),
            "roles": role_counts
        }, status=status.HTTP_200_OK)