# users/tests/test_auth.py
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_user_login(setup_users):
    """Test store owner can login successfully"""
    client = setup_users['client']
    login_data = {
        "email": "abc1@gmail.com",
        "password": "testpassword",
    }
    response = client.post(reverse("users:login"), login_data)
    token = response.data["auth_token"]
    assert response.status_code == status.HTTP_200_OK
    assert "auth_token" in response.data
    store_manager_user_id = setup_users["store_manager_user_id"]
    inventory_manager_user_id = setup_users["inventory_manager_user_id"]
    response = client.post(
        reverse("users:users-assign-store-owner"),  # Note the format: viewset-name-action-name
        data={},  # Add empty data dict since it's the first store owner
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "No user IDs provided."
    
    #test assignment of roles by the store owner to an already existing role
    response = client.post(
        reverse("users:users-assign-store-manager"),  # Note the format: viewset-name-action-name
        data={"user_ids":[inventory_manager_user_id,]}, 
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.get(
        reverse("users:staff-get-staff-members"),  # Note the format: viewset-name-action-name
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"response data after get staff roles summary: {response.data}")
    

@pytest.mark.django_db
def test_authorized_access(setup_users):
    """Test authorized access to protected resources"""
    client = setup_users['client']
    login_data = {
        "email": "abc1@gmail.com",
        "password": "testpassword",
    }
    response = client.post(reverse("users:login"), login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "auth_token" in response.data
    token = response.data["auth_token"]
    response = client.get("/auth/users/me",  HTTP_AUTHORIZATION=f"Token {token}", follow=True)
    assert response.status_code == status.HTTP_200_OK
    
@pytest.mark.django_db
def test_invalid_login(setup_users):
    """Test invalid login credentials"""
    client = setup_users['client']
    login_data = {
        "email": "wrong@gmail.com",
        "password": "wrongpassword",
    }
    response = client.post(reverse("users:login"), login_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_unauthorized_access(setup_users):
    """Test unauthorized access to protected resources"""
    client = setup_users['client']
    response = client.get("/auth/users/me", follow=True)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_user_logout(setup_users):
    """Test store owner can logout successfully"""
    client = setup_users['client']
    login_data = {
        "email": "abc1@gmail.com",
        "password": "testpassword",
    }
    response = client.post(reverse("users:login"), login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "auth_token" in response.data
    token = response.data["auth_token"]

    # Log out
    response = client.post(
        reverse("users:logout"),
        HTTP_AUTHORIZATION=f"Token {token}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Attempt to access user details after logout
    response = client.get(
        "/auth/users/me", HTTP_AUTHORIZATION=f"Token {token}", follow=True
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestRoleAssignments:
    """
    Test suite for the shoe shop role assignment API views.
    
    This suite covers the functionality of assigning and dismissing roles via API endpoints,
    ensuring proper permissions are enforced.
    
    Roles Hierarchy:
    - Store Owner (highest)
    - Store Manager
    - Inventory Manager
    - Sales Associate
    - Customer Service
    """
    @pytest.fixture(autouse=True)
    def setup(self, setup_users):
        self.client = setup_users["client"]
        self.store_owner_token = setup_users["store_owner_token"]
        self.store_owner_user_id = setup_users["store_owner_user_id"]

        self.store_manager_token = setup_users["store_manager_token"]
        self.store_manager_user_id = setup_users["store_manager_user_id"]

        self.inventory_manager_token = setup_users["inventory_manager_token"]
        self.inventory_manager_user_id = setup_users["inventory_manager_user_id"]

        self.sales_associate_token = setup_users["sales_associate_token"]
        self.sales_associate_user_id = setup_users["sales_associate_user_id"]

        self.customer_service_token = setup_users["customer_service_token"]
        self.customer_service_user_id = setup_users["customer_service_user_id"]
    @pytest.mark.parametrize(
        "assign_endpoint, user_id, token, expected_status",
        [
            # Store Owner can assign all roles
            (
                "users-assign-store-owner",
                "store_manager_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            (
                "users-assign-store-manager",
                "inventory_manager_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            (
                "users-assign-inventory-manager",
                "sales_associate_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            # Store Manager can assign lower roles
            (
                "users-assign-sales-associate",
                "customer_service_user_id",
                "store_manager_token",
                status.HTTP_200_OK,
            ),
            (
                "users-assign-customer-service",
                "sales_associate_user_id",
                "store_manager_token",
                status.HTTP_200_OK,
            ),
            # Invalid assignments - testing permissions
             (
                "users-assign-store-owner",
                "store_manager_user_id",
                "store_manager_token",
                status.HTTP_403_FORBIDDEN
            ),
            (
                "users-assign-store-manager",
                "customer_service_user_id",
                "store_manager_token",
                status.HTTP_403_FORBIDDEN,
            ),
            (
                "users-assign-inventory-manager",
                "customer_service_user_id",
                "inventory_manager_token",
                status.HTTP_403_FORBIDDEN,
            ),
            (
                "users-assign-sales-associate",
                "customer_service_user_id",
                "sales_associate_token",
                status.HTTP_403_FORBIDDEN,
            ),
        ],
    )
    def test_assign_roles(self, assign_endpoint, user_id, token, expected_status):
        """Test role assignment scenarios."""
        user_ids = [getattr(self, user_id)]
        
        # Retrieve the token value and associated user ID
        token_value = getattr(self, token)
        user_id_value = getattr(self, user_id)
        
        # Debug: Print the token and user details
        print(f"Using token: {token_value}")
        print(f"User ID for token: {user_id_value}")

        # Perform the request
        response = self.client.post(
            reverse(f"users:{assign_endpoint}"),
            {"user_ids": user_ids},
            HTTP_AUTHORIZATION=f"Token {token_value}"
        )

        # Debug: Print response data for clarity
        print(f"Response data: {response.data}")
        print(f"Response status code: {response.status_code}")
        
        # Assert the expected status code
        assert response.status_code == expected_status
    
    
    @pytest.mark.parametrize(
        "dismiss_endpoint, user_id, token, expected_status",
        [
            # Store Owner can dismiss any role
            (
                "users-dismiss-role",
                "store_manager_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            (
                "users-dismiss-role",
                "inventory_manager_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            (
                "users-dismiss-role",
                "sales_associate_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            (
                "users-dismiss-role",
                "customer_service_user_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            # Invalid dismissals - testing permissions
            (
                "users-dismiss-role",
                "store_manager_user_id",
                "store_manager_token",
                status.HTTP_403_FORBIDDEN,
            ),
            (
                "users-dismiss-role",
                "inventory_manager_user_id",
                "inventory_manager_token",
                status.HTTP_403_FORBIDDEN,
            ),
            (
                "users-dismiss-role",
                "sales_associate_user_id",
                "store_manager_token",
                status.HTTP_403_FORBIDDEN,
            ),
        ],
    )
    def test_dismiss_roles(self, dismiss_endpoint, user_id, token, expected_status):
        """Test role dismissal scenarios."""
        user_ids = [getattr(self, user_id)]
        response = self.client.post(
            reverse(f"users:{dismiss_endpoint}"),
            {"user_ids": user_ids},
            HTTP_AUTHORIZATION=f"Token {getattr(self, token)}"
        )
        print(f"Response data: {response.data}")
        assert response.status_code == expected_status