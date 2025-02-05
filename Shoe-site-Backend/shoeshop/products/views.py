from django.conf import settings
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError
from products.models import Category, CategoryStatusChoices
from products.serializers import CategoryCreateUpdateSerializer, CategorySerializer
from users.permissions import IsInventoryManager

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Category objects.

    Provides CRUD operations for categories and additional endpoints for hierarchy navigation.
    The default GET operations return only active categories. Use a query parameter
    (e.g. is_active=false) to retrieve inactive or all categories.
    """
    
    queryset = Category.objects.all().prefetch_related('children')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Returns a filtered queryset based on query parameters.
        By default, only active categories are returned unless the query parameter 
        `is_active` is provided (e.g., ?is_active=false or ?is_active=all).
        Query Parameters:
        - is_active (str, optional): Filter categories based on their active status. 
          If not provided, only active categories are returned. If 'all', all categories 
          are returned. If 'true' or 'false', categories are filtered based on the 
          boolean value.
        - parent_id (int, optional): Filter categories based on their parent ID.
        Returns:
        - QuerySet: A filtered queryset of categories.
        """
        queryset = super().get_queryset()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is None:
            # Default: return only active categories
            queryset = queryset.filter(status=CategoryStatusChoices.ACTIVE)
        elif is_active.lower() != 'all':
            # If explicitly provided, filter based on the provided boolean value.
            queryset = queryset.filter(status=is_active.lower() == 'true' and CategoryStatusChoices.ACTIVE or CategoryStatusChoices.INACTIVE)
            
        # Optional filtering by parent can be done as well.
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
            
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsInventoryManager]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        """
        Update a category. This method also supports updating the category status.
        
        If the request data contains a 'status' field, the method:
        - Checks if the new status is among the allowed choices.
        - Compares it with the current status.
        - If they differ, updates the status field.
        The model's clean() method will ensure that validations are performed.
        
        Returns:
            Response: Updated category data or error message.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check for status update in the request data.
        if 'status' in request.data:
            new_status = request.data['status']
            # Validate that new_status is among allowed choices.
            if new_status not in CategoryStatusChoices.values:
                return Response(
                    {"error": f"Invalid status. Allowed statuses are: {', '.join(CategoryStatusChoices.values)}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # If the new status is different, update it.
            if instance.status != new_status:
                instance.status = new_status
                try:
                    instance.clean()  # Perform model validations.
                except ValidationError as e:
                    return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        
        # Proceed with normal update for other fields.
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def hierarchy(self, request) -> Response:
        """
        Retrieve the category hierarchy starting from top-level categories.
        
        **Query Parameters:**
            - depth (int, optional): The maximum depth of hierarchy to return.
              Defaults to 1. If greater than CATEGORY_MAX_DEPTH, returns up to the max depth.
        
        **Returns:**
            Response (JSON): A serialized representation of category hierarchy.
        """
        try:
            max_depth = getattr(settings, "CATEGORY_MAX_DEPTH", 3)
            requested_depth = request.query_params.get("depth", 1)
            try:
                depth = int(requested_depth)
                if depth < 0:
                    raise ValueError
            except ValueError:
                return Response(
                    {"error": "Depth parameter must be a non-negative integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if depth > 0:
                depth = min(depth, max_depth)
            top_level_categories = Category.objects.filter(parent__isnull=True)
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
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs) -> Response:
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"message": "Category successfully deleted"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
