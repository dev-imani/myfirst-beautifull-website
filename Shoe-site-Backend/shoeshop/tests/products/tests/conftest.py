import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.choices import SexChoices
from users.utils import todays_date
from products.choices import CategoryChoices


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
    }
    store_owner_login_data = {
        "email": "abc1@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/", store_owner_data)
    store_owner_user_id = response.data["id"]
    
    # Retrieve the token after login
    response = client.post(reverse("users:login"), store_owner_login_data)
    store_owner_token = response.data["auth_token"]
    
    #assign store owner role
    response = client.post(
        reverse("users:users-assign-store-owner"),  # Note the format: viewset-name-action-name
        data={},  # Add empty data dict since it's the first store owner
        HTTP_AUTHORIZATION=f"Token {store_owner_token}"
    )
    
    # Create store manager user
    store_manager_data = {
        "username": "store_manager",
        "email": "abc2@gmail.com",
        "password": "testpassword",
        "first_name": "store",
        "last_name": "Manager",
        "phone_number": "+254755555555",
        "sex": SexChoices.MALE,
    }
    store_manager_login_data = {
        "email": "abc2@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/", store_manager_data)
   
    store_manager_user_id = response.data["id"]
    
    # Retrieve the token after login
    response = client.post(reverse("users:login"), store_manager_login_data)
    store_manager_token = response.data["auth_token"]
    
    #assign storemanager role
    response = client.post(
        reverse("users:users-assign-store-manager"),  # Note the format: viewset-name-action-name
        data={"user_ids":[store_manager_user_id,]}, 
        HTTP_AUTHORIZATION=f"Token {store_owner_token}"
    )
    
    # Create inventory manager user
    inventory_manager_data = {
        "username": "inventorymanager",
        "email": "abc3@gmail.com",
        "password": "testpassword",
        "first_name": "Inventory",
        "last_name": "Manager",
        "phone_number": "+254744444444",
        "sex": SexChoices.FEMALE,
    }
    inventory_manager_login_data = {
        "email": "abc3@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/",inventory_manager_data)
    inventory_manager_user_id = response.data["id"]
    # Retrieve the token after login
    response = client.post(reverse("users:login"), inventory_manager_login_data)
    inventory_manager_token = response.data["auth_token"]
   
    #assign inventory manager role
    response = client.post(
        reverse('users:users-assign-inventory-manager'),  # Note the format: viewset-name-action-name
        data={"user_ids":[inventory_manager_user_id,]}, 
        HTTP_AUTHORIZATION=f"Token {store_manager_token}"
    )
    

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

    #assign sales associate role
    response = client.post(
        reverse("users:users-assign-sales-associate"),  # Note the format: viewset-name-action-name
        data={"user_ids":[sales_associate_user_id,]}, 
        HTTP_AUTHORIZATION=f"Token {store_manager_token}"
    )
   
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
    
    #assign customer service role
    response = client.post(
        reverse("users:users-assign-customer-service"),  # Note the format: viewset-name-action-name
        data={"user_ids":[customer_service_user_id,]}, 
        HTTP_AUTHORIZATION=f"Token {store_manager_token}"
    )

    #create a user
    store_user_data = {
        "username": "user",
        "email": "abc0@gmail.com",
        "password": "testpassword",
        "first_name": "store",
        "last_name": "User",
        "phone_number": "+254787654441",
        "sex": SexChoices.MALE,
    }
    store_user_login_data = {
        "email": "abc0@gmail.com",
        "password": "testpassword",
    }
    response = client.post("/auth/users/", store_user_data)
   
    # Retrieve the token after login
    response = client.post(reverse("users:login"), store_user_login_data)
    store_user_token = response.data["auth_token"]

    return {
        "client": client,
        "store_user_token": store_user_token,
        "store_owner_token": store_owner_token,
        "store_owner_user_id": store_owner_user_id,
        "store_manager_token": store_manager_token,
        "store_manager_user_id": store_manager_user_id,
        "inventory_manager_token": inventory_manager_token,
        "inventory_manager_user_id": inventory_manager_user_id,
        "sales_associate_token": sales_associate_token,
        "sales_associate_user_id": sales_associate_user_id,
        "customer_service_token": customer_service_token,
        "customer_service_user_id": customer_service_user_id,
    }

@pytest.fixture()
def setup_category(setup_users):
    client = setup_users["client"]
    token = setup_users["inventory_manager_token"]

    # Create a category
    category_data = {
        "name": "Shoes",
        "description": "Shoes for all ages",
        "top_level_category": "shoes",
    }
    response = client.post(
        reverse("products:categories-list"),  # Use -list for creating
        category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"response in conftest after creation::  f{response.data} status {response.status_code}")
    
    shoes_category_id = response.data["id"]

    if response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating category: {response.data}")
        pytest.fail("Category creation failed in fixture") #fail the test if category creation fails
    category_data = {
        "name": "men's",
        "description": "Shoes for men",
        "parent": shoes_category_id,
    }
    response = client.post(
        reverse("products:categories-list"),  # Use -list for creating
        category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )

    print(f"response in conftest after creation::  f{response.data} status {response.status_code}")
    mens_shoe_category_id = response.data["id"]
    category_data = {
        "name": "women's",
        "description": "Shoes for women",
        "parent": shoes_category_id,
    }
    response = client.post(
        reverse("products:categories-list"),  # Use -list for creating
        category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    
    print(f"response in conftest after creation::  f{response.data} status {response.status_code}")
    womens_shoe_category_id = response.data["id"]

    category_data = {
        "name": "boots",
        "description": "boots for women",
        "parent": womens_shoe_category_id,
    }
    response = client.post(
        reverse("products:categories-list"),  # Use -list for creating
        category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"response after womens boot: {response.data}")

    womenboots_shoe_category_id = response.data["id"]
    
    
    return {
        "client": client,
        "token": token,
        "shoe_top_level_category_id": shoes_category_id, # return the id
        "mens_id": mens_shoe_category_id,
        "womens_id": womens_shoe_category_id,
        "womenboots_id": womenboots_shoe_category_id,
    }

