from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.exceptions import ValidationError
from products.models import Category
from products.serializers import CategoryCreateUpdateSerializer, CategorySerializer
from users.permissions import IsStoreOwner, IsStoreManager, IsStoreStaff, IsInventoryManager
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Category objects.
    
    Provides CRUD operations for categories and additional endpoints for hierarchy navigation.
    Includes prefetch_related optimization for children relationships.
    
    Permissions:
    - Read operations (list, retrieve) are available to all users
    - Write operations (create, update, delete) require authentication
    """
    
    queryset = Category.objects.all().prefetch_related('children')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """
        Get the list of categories for this view.
        
        Implements custom filtering based on query parameters and optimizes
        database queries using prefetch_related.
        
        Returns:
            QuerySet: Filtered queryset of Category objects
        """
        queryset = super().get_queryset()
        
        # Add custom filtering based on query parameters
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
            
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategorySerializer

    def get_permissions(self):
        """
        Customize permissions based on action.
        
        Returns:
            list: List of permission classes
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsInventoryManager]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    
    @action(detail=False, methods=['GET'])
    def hierarchy(self, request) -> Response:
        """
        Retrieve the category hierarchy starting from top-level categories.

        **Args:**
            request (Request): HTTP request object containing query parameters.

        **Query Parameters:**
            - `depth` (int, optional): The maximum depth of hierarchy to return.
              Defaults to 1. If greater than `CATEGORY_MAX_DEPTH`, returns up to the max depth.

        **Returns:**
            Response (JSON): A serialized representation of category hierarchy.

        **Raises:**
            - `ValidationError`: If `depth` is invalid (not a positive integer).
            - `HTTP_500_INTERNAL_SERVER_ERROR`: If any other unexpected error occurs.

        **Example Request:**
            ```
            GET /api/categories/hierarchy/?depth=2
            ```

        **Example Response:**
            ```json
            [
                {
                    "id": 1,
                    "name": "Electronics",
                    "slug": "electronics",
                    "description": "Electronics category",
                    "parent": null,
                    "children": [
                        {
                            "id": 2,
                            "name": "Phones",
                            "slug": "phones",
                            "description": "Mobile phones",
                            "parent": 1,
                            "children": [
                                {
                                    "id": 3,
                                    "name": "Smartphones",
                                    "slug": "smartphones",
                                    "description": "Modern smartphones",
                                    "parent": 2,
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            ]
            ```
        """
        try:
            # Get max depth from settings, default to 3 if not set
            max_depth = getattr(settings, "CATEGORY_MAX_DEPTH", 3)

            # Parse depth from request, ensure it's a positive integer
            requested_depth = request.query_params.get("depth", 1)
            try:
                depth = int(requested_depth)
                if depth < 1:
                    raise ValueError
            except ValueError:
                return Response(
                    {"error": "Depth parameter must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure depth does not exceed system-defined max depth
            depth = min(depth, max_depth)

            # Get all top-level categories (parent is NULL)
            top_level_categories = Category.objects.filter(parent__isnull=True)

            # Serialize with a dynamic depth context
            serializer = CategorySerializer(
                top_level_categories,
                many=True,
                context={'depth': depth, 'request': request}
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs) -> Response:
        """
        Create a new category with error handling.
        
        Returns:
            Response: Newly created category data or error message
        """
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 

    def update(self, request, *args, **kwargs) -> Response:
        """
        Update a category with error handling.
        
        Returns:
            Response: Updated category data or error message
        """
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs) -> Response:
        """
        Delete a category with error handling.
        
        Returns:
            Response: Success message or error details
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"message": "Category successfully deleted"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )