from django.urls import path, include
from rest_framework import routers

from products.views import CategoryViewSet

# Set the app name for namespacing
app_name = "products"

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
# Define URL patterns for the 'users' app
urlpatterns = [
    path("", include(router.urls)),
]