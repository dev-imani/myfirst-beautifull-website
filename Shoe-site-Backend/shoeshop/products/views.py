from django.conf import settings
import django_filters
from django.db import transaction
from django.db.models import Prefetch, Sum
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets, filters, status,serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError, NotFound, ParseError
from products.models import BaseProduct, Category, Brand, ClothingProduct, ClothingVariant, ProductImage, ShoeColor, ShoeProduct, ShoeSize, ShoeVariant
from products.choices import CategoryStatusChoices
from products.serializers import BaseProductSerializer, BrandSerializer, CategoryCreateUpdateSerializer, CategorySerializer, ClothingProductSerializer, ClothingVariantSerializer, ShoeProductSerializer, ShoeVariantSerializer
from products.product_mapper import ProductMapper
from users.permissions import IsInventoryManager

class CategoryViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing Category objects.

    Provides CRUD operations for categories and additional endpoints for hierarchy navigation.
    The default GET operations return only active categories. Use a query parameter
    (e.g., ?is_active=false) to retrieve inactive or all categories.

    Attributes:
        queryset (QuerySet): The queryset of Category objects.
        serializer_class (Serializer): The serializer class used for serialization.
        filter_backends (list): The list of filter backends used for filtering the queryset.
        search_fields (list): The list of fields used for search filtering.
        ordering_fields (list): The list of fields used for ordering.

    Methods:
        get_queryset(): Returns a filtered queryset based on query parameters.
        get_serializer_class(): Returns the appropriate serializer class based on the action.
        get_permissions(): Returns the appropriate permission classes based on the action.
        update(request, *args, **kwargs): Updates a category instance.
        hierarchy(request): Retrieves the category hierarchy starting from top-level categories.

    Example:
        >>> from rest_framework.test import APIClient
        >>> client = APIClient()
        >>> response = client.get('/categories/')
        >>> print(response.json())
        [{'id': 1, 'name': 'Root Category', ...}]

    Note:
        The `hierarchy` endpoint supports a `depth` query parameter to control the depth of the hierarchy.

    See Also:
        CategorySerializer: The serializer used for serializing Category objects.
        CategoryCreateUpdateSerializer: The serializer used for creating
    """
    
    queryset = Category.objects.all().prefetch_related('children')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """
        Returns a filtered queryset based on query parameters.

        By default, only active categories are returned unless the query parameter
        `is_active` is provided (e.g., ?is_active=false or ?is_active=all).
        Query Parameters:
            - is_active (str, optional): Filter categories based on their active status.
              If not provided, only active categories are returned. If 'all', all categories
              are returned. If 'true' or 'false', categories are filtered based on the
              boolean value.
            - parent_id (int, optional): Filter categories based on their parent ID.

        Returns:
            QuerySet: A filtered queryset of categories.
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
        """
        Returns the appropriate serializer class based on the action.

        If the action is 'create', 'update', or 'partial_update', returns
        CategoryCreateUpdateSerializer. Otherwise, returns CategorySerializer.

        Returns:
            Serializer: The appropriate serializer class.
        """
        
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
    """
    A ViewSet for managing Brand objects.

    Provides CRUD operations for brands.

    Attributes:
        queryset (QuerySet): The queryset of Brand objects.
        serializer_class (Serializer): The serializer class used for serialization.
        filter_backends (list): The list of filter backends used for filtering the queryset.
        filterset_class (FilterSet): The filter set class used for filtering the queryset.

    Methods:
        get_permissions(): Returns the appropriate permission classes based on the action.

    Example:
        >>> from rest_framework.test import APIClient
        >>> client = APIClient()
        >>> response = client.get('/brands/')
        >>> print(response.json())
        [{'id': 1, 'name': 'Test Brand', ...}]

    See Also:
        BrandSerializer: The serializer used for serializing Brand objects.
        BrandFilter: The filter set used for filtering Brand objects.
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
    A ViewSet for managing Product objects.

    Provides CRUD operations for products and additional endpoints for managing product variants and inventory.

    Attributes:
        permission_classes (list): The list of permission classes used for access control.

    Methods:
        get_permissions(): Returns the appropriate permission classes based on the action.
        get_queryset(): Returns a filtered queryset based on query parameters.
        get_serializer_class(): Returns the appropriate serializer class based on the action.
        get_serializer_context(): Returns the serializer context.
        create(request, *args, **kwargs): Creates a new product instance.
        update(request, *args, **kwargs): Updates a product instance.
        variants(request, pk=None): Retrieves all variants for a specific product.
        inventory(request, pk=None): Retrieves detailed inventory information for a product.
        update_stock(request, pk=None): Updates stock levels for product variants.

    Example:
        >>> from rest_framework.test import APIClient
        >>> client = APIClient()
        >>> response = client.get('/products/?category=1')
        >>> print(response.json())
        [{'id': 1, 'name': 'Test Product', ...}]

    Note:
        The `create` and `update` methods support bulk operations.
        The `get_queryset` method expects either a `category` query parameter or a `pk` in the URL.

    See Also:
        BaseProductSerializer: The serializer used for serializing BaseProduct objects.
        ShoeProductSerializer: The serializer used for serializing ShoeProduct objects.
        ClothingProductSerializer: The serializer used for serializing ClothingProduct objects.
        ShoeVariantSerializer: The serializer used for serializing ShoeVariant objects.
        ClothingVariantSerializer: The serializer used for serializing ClothingVariant objects.
    """
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'update_stock']:
            permission_classes = [IsInventoryManager]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        """
        Dynamically fetches the correct product model based on `prod_type` (if querying by `pk`)
        or category-based inference.

        This method supports two main query types:
        1. Fetch by primary key (`pk`), which requires specifying the product type (`prod_type`).
        2. Fetch by category, which infers the product type based on the category's root.

        Args:
            self: The view instance.

        Returns:
            QuerySet: A Django QuerySet containing the filtered product objects.

        Raises:
            ParseError: If the query parameters are invalid or missing required fields.
            NotFound: If the specified category does not exist.
        """
        # Extract query parameters
        pk = self.kwargs.get('pk')
        category_id = self.request.query_params.get('category')
        prod_type = self.request.query_params.get('prod_type')

        # Define optimized querysets
        product_models = {
            "shoes": ShoeProduct.objects.select_related(
                'brand', 
                'category'
            ).prefetch_related(
                Prefetch(
                    'images',
                    queryset=ProductImage.objects.only('id', 'image', 'alt_text')
                ),
                Prefetch(
                    'sizes',
                    queryset=ShoeSize.objects.only('id', 'size')
                ),
                Prefetch(
                    'colors',
                    queryset=ShoeColor.objects.only('id', 'color')
                ),
                Prefetch(
                    'variants',
                    queryset=ShoeVariant.objects.only(
                        'id', 'product_id', 'size', 'color', 'stock'
                    )
                )
            ),
            
            "clothing": ClothingProduct.objects.select_related(
                'brand',
                'category'
            ).prefetch_related(
                Prefetch(
                    'images',
                    queryset=ProductImage.objects.only('id', 'image', 'alt_text')
                ),
                Prefetch(
                    'variants',
                    queryset=ClothingVariant.objects.only(
                        'id', 'product_id', 'size', 'stock'
                    )
                )
            )
        }

        if pk:
            if not prod_type or prod_type not in product_models:
                raise ParseError(
                    "Missing or invalid 'prod_type' when querying by 'pk'."
                )
            return product_models[prod_type].filter(pk=pk)

        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                model = ProductMapper.get_model_for_category(category)
                if not model:
                    raise ParseError("Unsupported category type.")
                
                # Get all descendants including the current category
                descendant_categories = category.get_descendants(include_self=True)
                descendant_category_ids = [cat.id for cat in descendant_categories]

                # Filter products based on the descendant categories
                return model.objects.filter(category__in=descendant_category_ids)
            except Category.DoesNotExist:
                raise NotFound("Category not found.")

        raise ParseError("Either 'category' or 'pk' (with 'prod_type') is required.")

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
            
        # For creating a new product
        creation_type = self.request.query_params.get('creation_type')
        if creation_type:
            serializer_class = ProductMapper.CATEGORY_TO_SERIALIZER.get(creation_type)
            if not serializer_class:
                raise ParseError("Invalid 'creation_type' query parameter.")
            return serializer_class

        # For listing products by category
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                serializer_class = ProductMapper.get_serializer_for_category(category)
                if not serializer_class:
                    raise ParseError("Invalid category type")
                return serializer_class
            except Category.DoesNotExist:
                raise NotFound("Category not found")
        
        raise ParseError("Either 'category', 'creation_type' or 'pk' parameter is required")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ['create', 'update', 'partial_update']:
            context['product'] = self.get_object() if self.kwargs.get('pk') else None
        return context

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Creates new product instances.
        Supports bulk creation of products of different types.
        """
        query_creation_type = self.request.query_params.get('creation_type')
        print("in viewsets and creation_type from query is+++++++++++", query_creation_type)

        if not query_creation_type:
            raise ParseError("The 'creation_type' query parameter is required.")

        # For bulk creation, the creation_type in query params is optional 
        # (will use individual product creation_types instead)
        valid_creation_types = ['shoes', 'clothing']
        
        # Handle both single item and list of items
        data = request.data
        is_many = isinstance(data, list)
        
        if not is_many:
            # Single product - validate against query param
            if query_creation_type not in valid_creation_types:
                raise ValidationError({
                    "creation_type": f"Invalid creation type. Allowed values are: {', '.join(valid_creation_types)}"
                })
                
            data_creation_type = data.get('creation_type')
            if data_creation_type and data_creation_type != query_creation_type:
                raise ValidationError({
                    "creation_type": "Creation type in query parameters does not match creation type in data"
                })
                
            serializer_class = ProductMapper.CATEGORY_TO_SERIALIZER.get(query_creation_type)
            print("in viewsets and data sent to serializers is" , data)
            serializer = serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            product = serializer.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            # Bulk creation - handle multiple products
            created_products = []
            
            for product_data in data:
                creation_type = product_data.get('creation_type')
                
                if not creation_type:
                    raise ValidationError({
                        "creation_type": "Creation type is required for each product in bulk creation"
                    })
                    
                if creation_type not in valid_creation_types:
                    raise ValidationError({
                        "creation_type": f"Invalid creation type '{creation_type}'. Allowed values are: {', '.join(valid_creation_types)}"
                    })
                    
                serializer_class = ProductMapper.CATEGORY_TO_SERIALIZER.get(creation_type)
                
                serializer = serializer_class(data=product_data)
                serializer.is_valid(raise_exception=True)
                product = serializer.save()
                created_products.append(serializer.data)
            
            return Response(created_products, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Updates a product instance.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except serializers.ValidationError as e:
            return Response({"validation_error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """
        Retrieves all variants for a specific product.

        URL Parameters:
            - pk (int): The primary key of the product.

        Returns:
            Response: The product variants.

        Raises:
            NotFound: If the product is not found.
        """        
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
        """
        Retrieves detailed inventory information for a product.

        URL Parameters:
            - pk (int): The primary key of the product.

        Returns:
            Response: The product inventory information.

        Raises:
            NotFound: If the product is not found.
        """
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
        """
        Updates stock levels for product variants.

        URL Parameters:
            - pk (int): The primary key of the product.

        Request Body:
            - variants (list): A list of variant data containing 'variant_id' and 'stock'.

        Returns:
            Response: The updated stock levels.

        Raises:
            ValidationError: If the request data is invalid.
            Exception: If an unexpected error occurs.
        """
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