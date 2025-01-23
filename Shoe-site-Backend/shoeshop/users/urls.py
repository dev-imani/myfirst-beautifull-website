from django.urls import path, include
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework import routers

from users.views import CustomUserViewSet, StaffMemberViewSet

# Set the app name for namespacing
app_name = "users"

router = routers.DefaultRouter()
router.register(r"", CustomUserViewSet, basename="users")
router.register(r"staff", StaffMemberViewSet, basename="staff")
# Define URL patterns for the 'users' app
urlpatterns = [
    # URL for user authentication (login)
    path("auth/login/", TokenCreateView.as_view(), name="login"),
    # URL for user logout
    path("auth/logout/", TokenDestroyView.as_view(), name="logout"),
    path("", include(router.urls)),
]