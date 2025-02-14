from django.conf import settings
import django_filters
from django.db import transaction
from django.db.models import Prefetch, Sum
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError, NotFound, ParseError
from products.models import BaseProduct, Category, Brand, ClothingProduct, ClothingVariant, ShoeColor, ShoeProduct, ShoeSize, ShoeVariant
from products.choices import CategoryStatusChoices
from products.serializers import BaseProductSerializer, BrandSerializer, CategoryCreateUpdateSerializer, CategorySerializer, ClothingProductSerializer, ClothingVariantSerializer, ShoeProductSerializer, ShoeVariantSerializer
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'update_stock']:
            permission_classes = [IsInventoryManager]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        category_id = self.request.query_params.get('category')

        base_qs = None
        if pk:
            # Try to find the product in both models with optimized queries
            try:
                shoe_qs = ShoeProduct.objects.filter(pk=pk).prefetch_related(
                    'images',
                    'sizes',
                    'colors',
                    Prefetch('variants', queryset=ShoeVariant.objects.all())
                ).select_related('brand', 'category')
                
                if shoe_qs.exists():
                    base_qs = shoe_qs
                else:
                    clothing_qs = ClothingProduct.objects.filter(pk=pk).prefetch_related(
                        'images',
                        Prefetch('variants', queryset=ClothingVariant.objects.all())
                    ).select_related('brand', 'category')
                    
                    if clothing_qs.exists():
                        base_qs = clothing_qs
                    else:
                        raise NotFound("Product not found")
            except Exception as e:
                raise NotFound(f"Error finding product: {str(e)}")

        elif category_id:
            try:
                category = Category.objects.get(pk=category_id)
                root_category = category.get_root()
                
                if root_category.name.lower() == "shoes":
                    base_qs = ShoeProduct.objects.filter(category=category)
                elif root_category.name.lower() == "clothing":
                    base_qs = ClothingProduct.objects.filter(category=category)
                else:
                    raise ParseError(" Invalid category type")
                    
                base_qs = base_qs.prefetch_related(
                    'images',
                    'variants'
                ).select_related('brand', 'category')
                
            except Category.DoesNotExist:
                raise NotFound("Category not found")
        else:
            raise ParseError("Either 'category' or 'pk' parameter is required")

        return base_qs.annotate(
            total_stock=Sum('variants__stock')
        )
        
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.kwargs.get('pk'):
            try:
                product = self.get_object()
                if isinstance(product, ShoeProduct):
                    return ShoeProductSerializer
                if isinstance(product, ClothingProduct):
                    return ClothingProductSerializer
            except Exception:
                raise NotFound("Product not found")

        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                root_category = category.get_root()
                
                if root_category.name.lower() == "shoes":
                    return ShoeProductSerializer
                elif root_category.name.lower() == "clothing":
                    return ClothingProductSerializer
                else:
                    raise ParseError("Invalid category type")
            except Category.DoesNotExist:
                raise NotFound("Category not found")
        
        raise ParseError("Either 'category' or 'pk' parameter is required")

    def get_serializer_context(self):
        """Add additional context to serializer."""
        context = super().get_serializer_context()
        if self.action in ['create', 'update', 'partial_update']:
            context['product'] = self.get_object() if self.kwargs.get('pk') else None
        return context

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            is_many = isinstance(request.data, list) # Check if request.data is a list

            serializer = self.get_serializer(data=request.data, many=is_many) # Pass many=True if it's a list
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer) # Use perform_create for bulk create and single create to handle saving logic in one place.
            headers = self.get_success_headers(serializer.data) # Get headers (might need adjustment for bulk)

            if is_many:
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers) # Return list of created data for bulk
            else:
                 return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers) # Return single data for single create


        except ValidationError as e:
            return Response(
                {"validation_error": e.detail if isinstance(e.detail, dict) else str(e)}, # Handle validation errors (now potentially a dict for bulk)
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer): # Centralized saving logic
        serializer.save()
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            product = serializer.save()
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {"validation_error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """Get all variants for a specific product."""
        product = self.get_object()
        
        if isinstance(product, ShoeProduct):
            variants = product.variants.all()
            serializer = ShoeVariantSerializer(variants, many=True)
        elif isinstance(product, ClothingProduct):
            variants = product.variants.all()
            serializer = ClothingVariantSerializer(variants, many=True)
        else:
            return Response(
                {"error": "Invalid product type"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get detailed inventory information for a product."""
        product = self.get_object()
        
        variants_data = []
        for variant in product.variants.all():
            variant_data = {
                'id': variant.id,
                'stock': variant.stock,
            }
            
            if isinstance(product, ShoeProduct):
                variant_data.update({
                    'size': variant.size,
                    'color': variant.color
                })
            else:  # ClothingProduct
                variant_data.update({
                    'size': variant.size
                })
                
            variants_data.append(variant_data)

        total_stock = sum(variant.stock for variant in product.variants.all())
        
        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'total_stock': total_stock,
            'variants': variants_data
        })

    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update stock levels for product variants."""
        try:
            product = self.get_object()
            variants_data = request.data.get('variants', [])
            
            if not variants_data:
                raise ValidationError("No variant data provided")

            updated_variants = []
            with transaction.atomic():
                for variant_data in variants_data:
                    variant_id = variant_data.get('variant_id')
                    new_stock = variant_data.get('stock')
                    
                    if variant_id is None or new_stock is None:
                        raise ValidationError(
                            "Both variant_id and stock are required for each variant"
                        )
                    
                    if new_stock < 0:
                        raise ValidationError("Stock cannot be negative")
                        
                    try:
                        variant = product.variants.get(id=variant_id)
                    except Exception:
                        raise ValidationError(f"Variant {variant_id} not found")
                        
                    variant.stock = new_stock
                    variant.save()
                    
                    updated_variants.append({
                        'variant_id': variant_id,
                        'new_stock': new_stock
                    })

            return Response({
                'message': 'Stock updated successfully',
                'updated_variants': updated_variants
            })
            
        except ValidationError as e:
            return Response(
                {"validation_error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )