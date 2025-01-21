from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Create a schema view for Swagger and ReDoc documentation
schema_view = get_schema_view(
    openapi.Info(
        title="SOLELY: Shoe Store & Marketplace API",
        default_version="v1",
        description="API for managing shoe store operations and enabling marketplace functionality, including user management, product catalog, orders, and more.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="mamesareagan0@gmail.com"),
        license=openapi.License(
            name="Apache License V2.0",
            url="https://www.apache.org/licenses/LICENSE-2.0",
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Define URL patterns for your Django project
urlpatterns = [
    # Include authentication URLs provided by Djoser
    path("auth/", include("djoser.urls")),
    path('auth/', include('djoser.urls.authtoken')),
    # Include URLs from the 'users' app, and set a namespace for clarity
    path("users/", include("users.urls", namespace="users")),
    # URL for Swagger documentation with UI
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    # # URL for ReDoc documentation with UI
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # For django debug tool bar
    path("__debug__/", include("debug_toolbar.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)