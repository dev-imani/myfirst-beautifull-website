import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.choices import SexChoices
from users.utils import todays_date


@pytest.fixture()
def setup_users():
    client = APIClient()

    # Create store  owner user
    store_owner_data = {
        "username": "owner",
        "email": "abc1@gmail.com",
        "password": "testpassword",
        "first_name": "store",
        "last_name": "Owner",
        "phone_number": "+254787654321",
        "sex": SexChoices.MALE,
        "is_store_owner": True,
    }
    store_owner_login_data = {
        "email": "abc1@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/", store_owner_data)
    store_owner_user_id = response.data["id"]
    print("store owner data after registration:", response.data)
    # Retrieve the token after login
    response = client.post(reverse("users:login"), store_owner_login_data)
    store_owner_token = response.data["auth_token"]
    print("Store owner data##### ::", response.data)
    # Create store manager user
    store_manager_data = {
        "username": "manager",
        "email": "abc2@gmail.com",
        "password": "testpassword",
        "first_name": "store",
        "last_name": "Manager",
        "phone_number": "+254755555555",
        "sex": SexChoices.MALE,
        "is_store_manager": True,
    }
    store_manager_login_data = {
        "email": "abc2@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/", store_manager_data)
    store_manager_user_id = response.data["id"]
    print("store manager data after registration:", response.data)
    # Retrieve the token after login
    response = client.post(reverse("users:login"), store_manager_login_data)
    store_manager_token = response.data["auth_token"]
    print("Store manager data##### ::", response.data)
    # Create inventory manager user
    inventory_manager_data = {
        "username": "inventorymanager",
        "email": "abc3@gmail.com",
        "password": "testpassword",
        "first_name": "Inventory",
        "last_name": "Manager",
        "phone_number": "+254744444444",
        "sex": SexChoices.FEMALE,
        "is_inventory_manager": True,
    }
    inventory_manager_login_data = {
        "email": "abc3@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/",inventory_manager_data)
    inventory_manager_user_id = response.data["id"]
    # Retrieve the token after login
    response = client.post(reverse("users:login"), inventory_manager_login_data)
    inventry_manager_token = response.data["auth_token"]
    print("Inventory manager data##### ::", response.data)

    # Create sales_associate user
    sales_associate_data = {
        "username": "salesassociate",
        "email": "abc4@gmail.com",
        "password": "testpassword",
        "first_name": "Sales",
        "last_name": "Associate",
        "phone_number": "+254733333333",
        "sex": SexChoices.MALE,
        "is_sales_associate": True,
    }
    sales_associate_login_data = {
        "email": "abc4@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/",sales_associate_data)
    sales_associate_user_id = response.data["id"]
    # Retrieve the token after login
    response = client.post(reverse("users:login"),sales_associate_login_data)
    assert response.status_code == status.HTTP_200_OK
    sales_associate_token = response.data["auth_token"]

    # Create customer service user
    customer_service_data = {
        "username": "customerservice",
        "email": "abc5@gmail.com",
        "password": "testpassword",
        "first_name": "Customer",
        "last_name": "Service",
        "phone_number": "+254722222222",
        "sex": SexChoices.FEMALE,
        "is_farm_worker": True,
    }
    customer_service_login_data = {
        "email": "abc5@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/", customer_service_data)
    customer_service_user_id = response.data["id"]
    # Retrieve the token after login
    response = client.post(reverse("users:login"), customer_service_login_data)
    customer_service_token = response.data["auth_token"]
    
    return {
        "client": client,
        "store_owner_token": store_owner_token,
        "store_owner_user_id": store_owner_user_id,
        "store_manager_token": store_manager_token,
        "store_manager_user_id": store_manager_user_id,
        "inventory_manager_token": inventry_manager_token,
        "inventory_manager_user_id": inventory_manager_user_id,
        "sales_associate_token": sales_associate_token,
        "sales_associate_user_id": sales_associate_user_id,
        "customer_service_token": customer_service_token,
        "customer_service_user_id": customer_service_user_id,
    }