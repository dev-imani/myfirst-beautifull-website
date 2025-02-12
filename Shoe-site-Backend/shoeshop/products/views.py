from django.conf import settings
import django_filters
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError, NotFound, ParseError
from products.models import BaseProduct, Category, Brand, ClothingProduct, ClothingVariant, ShoeColor, ShoeProduct, ShoeSize, ShoeVariant
from products.choices import CategoryStatusChoices
from products.serializers import BaseProductSerializer, BrandSerializer, CategoryCreateUpdateSerializer, CategorySerializer, ClothingProductSerializer, ClothingVariantSerializer, ProductImageSerializer, ShoeProductSerializer, ShoeVariantSerializer
from products.product_mapper import ProductMapper
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

class BrandFilter(FilterSet):
    """BrandFilter is a filter class for the Brand model, allowing for filtering based on the following fields:
    - name: A case-insensitive contains filter for the brand name.
    - popularity: A range filter for the brand's popularity.
    - created_at: A date range filter for the brand's creation date.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')  # Case-insensitive contains for name
    popularity = django_filters.RangeFilter()  # Range filter for popularity
    created_at = django_filters.DateFromToRangeFilter()  # Date range filter for created_at

    class Meta:
        """
        Meta class for the Brand model form.

        Attributes:
            model (django.db.models.Model): The model associated with the form.
            fields (list): The list of fields to include in the form.
        """
        model = Brand
        fields = ['name', 'popularity', 'created_at']

class BrandViewSet(viewsets.ModelViewSet):
    """BrandViewSet is a view set for handling CRUD operations on the Brand model.

    Attributes:
        queryset (QuerySet): The set of Brand objects to operate on.
        serializer_class (Serializer): The serializer class used to validate and serialize Brand objects.
        permission_classes (list): The list of permission classes that determine access control.
        filter_backends (list): The list of filter backends used for filtering the queryset.
        filterset_class (FilterSet): The filter set class used for filtering the queryset.

    Methods:
        list(request, *args, **kwargs): Retrieve a list of Brand objects.
        create(request, *args, **kwargs): Create a new Brand object.
        retrieve(request, *args, **kwargs): Retrieve a specific Brand object by its ID.
        update(request, *args, **kwargs): Update a specific Brand object by its ID.
        partial_update(request, *args, **kwargs): Partially update a specific Brand object by its ID.
        destroy(request, *args, **kwargs): Delete a specific Brand object by its ID.
    """
    queryset = Brand.objects.all() # pylint: disable=no-member
    serializer_class = BrandSerializer
    permission_classes = [IsInventoryManager]

    filter_backends = [DjangoFilterBackend]
    filterset_class = BrandFilter
   
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsInventoryManager]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products (shoes and clothing).
    
    Provides standard CRUD operations and additional actions for managing product attributes.
    All nested data (variants, images, sizes, colors) can be managed through the main
    create/update endpoints using nested serializers.
    """
    
    def get_queryset(self):
        """
        Get the list of products filtered by category or specific product ID.
        
        Query Parameters:
            category (int): Filter products by category ID
            
        Returns:
            QuerySet: Filtered queryset of products
        """
        pk = self.kwargs.get('pk')
        category_id = self.request.query_params.get('category')

        if pk:
            try:
                # Try to find the product in either model
                try:
                    return ShoeProduct.objects.filter(pk=pk)
                except ShoeProduct.DoesNotExist:
                    return ClothingProduct.objects.filter(pk=pk)
            except Exception:
                raise NotFound({"error": "Product not found"})

        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                model = ProductMapper.get_model_for_category(category)
                return model.objects.filter(category=category) if model else ShoeProduct.objects.none()
            except Category.DoesNotExist:
                raise NotFound({"error": "Category not found"})

         # Raise an exception if no filters are provided
        raise ParseError({"error": "A 'category' ID or a 'pk' (product ID) must be provided."})

    def get_serializer_class(self):
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                return ProductMapper.get_serializer_for_category(category)
            except Category.DoesNotExist:
                raise NotFound({"error": "Category not found"})

        if self.kwargs.get('pk'):
            try:
                product = self.get_object()
                if isinstance(product, ShoeProduct):
                    return ShoeProductSerializer
                if isinstance(product, ClothingProduct):
                    return ClothingProductSerializer
            except Exception:
                raise NotFound({"error": "Product not found"})

        raise ParseError({"error": "Either 'pk' (product ID) or 'category' ID must be provided."})

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new product with all its related data (variants, images, etc.).
        
        The nested serializers handle the creation of related objects automatically.
        """
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Update a product and its related data (variants, images, etc.).
        
        The nested serializers handle the updating of related objects automatically.
        """
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete a product and all its related data."""
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """
        Get all variants for a product.
        
        Returns:
            List of variants with their details (size, color, stock)
        """
        product = self.get_object()
        if isinstance(product, ShoeProduct):
            serializer = ShoeVariantSerializer(product.variants.all(), many=True)
        elif isinstance(product, ClothingProduct):
            serializer = ClothingVariantSerializer(product.variants.all(), many=True)
        else:
            return Response({"error": "Invalid product type"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """
        Get inventory details for a product.
        
        Returns:
            Total stock and stock by variant
        """
        product = self.get_object()
        total_stock = sum(variant.stock for variant in product.variants.all())
        variants_stock = [{
            'id': variant.id,
            'size': variant.size,
            'color': variant.color if hasattr(variant, 'color') else None,
            'stock': variant.stock
        } for variant in product.variants.all()]
        
        return Response({
            'total_stock': total_stock,
            'variants': variants_stock
        })

    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """
        Update stock for product variants.
        
        Request Data:
            variants (list): List of dictionaries with variant_id and new stock value
            Example: [{"variant_id": 1, "stock": 10}, {"variant_id": 2, "stock": 5}]
        """
        try:
            product = self.get_object()
            variants_data = request.data.get('variants', [])
            
            updated_variants = []
            with transaction.atomic():
                for variant_data in variants_data:
                    variant_id = variant_data.get('variant_id')
                    new_stock = variant_data.get('stock')
                    
                    if variant_id is None or new_stock is None:
                        raise ValidationError({"error": "Missing variant_id or stock"})
                    
                    variant = product.variants.get(id=variant_id)
                    variant.stock = new_stock
                    variant.save()
                    updated_variants.append({
                        'variant_id': variant_id,
                        'stock': new_stock
                    })
                    
            return Response({
                'message': 'Stock updated successfully',
                'updated_variants': updated_variants
            })
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

