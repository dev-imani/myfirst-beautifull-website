from django.urls import path, include
from rest_framework import routers

from products.views import CategoryViewSet, BrandViewSet, ProductViewSet

# Set the app name for namespacing
app_name = "products"

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"brands", BrandViewSet, basename="brands" )
router.register(r'products', ProductViewSet, basename='product')
# Define URL patterns for the 'users' app
urlpatterns = [
    path("", include(router.urls)),
]