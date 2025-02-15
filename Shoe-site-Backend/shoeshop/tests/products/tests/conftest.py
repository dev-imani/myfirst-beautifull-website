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

    # --- Create Top-Level Categories ---
    # Shoes Category
    shoes_category_data = {
        "name": "Shoes",
        "description": "Shoes for all ages",
        "top_level_category": "shoes",
    }
    shoes_response = client.post(
        reverse("products:categories-list"),
        shoes_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response in conftest after creating 'Shoes' category: {shoes_response.data} status {shoes_response.status_code}")
    if shoes_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Shoes' category: {shoes_response.data}")
        pytest.fail("Category 'Shoes' creation failed in fixture")
    shoes_category_id = shoes_response.data["id"]

    # Clothing Category
    clothing_category_data = {
        "name": "Clothing",
        "description": "Clothing for all styles",
        "top_level_category": "clothing",
    }
    clothing_response = client.post(
        reverse("products:categories-list"),
        clothing_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response in conftest after creating 'Clothing' category: {clothing_response.data} status {clothing_response.status_code}")
    if clothing_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Clothing' category: {clothing_response.data}")
        pytest.fail("Category 'Clothing' creation failed in fixture")
    clothing_category_id = clothing_response.data["id"]

    # --- Create Child Categories under Shoes ---
    # Men's Shoes
    mens_shoe_category_data = {
        "name": "Men's",
        "description": "Shoes for men",
        "parent": shoes_category_id,
    }
    mens_shoes_response = client.post(
        reverse("products:categories-list"),
        mens_shoe_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response in conftest after creating 'Men's Shoes' category: {mens_shoes_response.data} status {mens_shoes_response.status_code}")
    if mens_shoes_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Men's Shoes' category: {mens_shoes_response.data}")
        pytest.fail("Category 'Men\'s Shoes' creation failed in fixture")
    mens_shoe_category_id = mens_shoes_response.data["id"]

    # Women's Shoes
    womens_shoe_category_data = {
        "name": "Women's",
        "description": "Shoes for women",
        "parent": shoes_category_id,
    }
    womens_shoes_response = client.post(
        reverse("products:categories-list"),
        womens_shoe_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response in conftest after creating 'Women's Shoes' category: {womens_shoes_response.data} status {womens_shoes_response.status_code}")
    if womens_shoes_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Women's Shoes' category: {womens_shoes_response.data}")
        pytest.fail("Category 'Women\'s Shoes' creation failed in fixture")
    womens_shoe_category_id = womens_shoes_response.data["id"]

    # Boots under Women's Shoes (example of a deeper level)
    womenboots_shoe_category_data = {
        "name": "Boots",
        "description": "Boots for women",
        "parent": womens_shoe_category_id,
    }
    womenboots_shoes_response = client.post(
        reverse("products:categories-list"),
        womenboots_shoe_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response after creating 'Boots' under Women's Shoes: {womenboots_shoes_response.data} status {womenboots_shoes_response.status_code}")
    if womenboots_shoes_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Boots' under Women's Shoes: {womenboots_shoes_response.data}")
        pytest.fail("Category 'Boots' under Women's Shoes creation failed in fixture")
    womenboots_shoe_category_id = womenboots_shoes_response.data["id"]


    # --- Create Child Categories under Clothing ---
    # Men's Clothing
    mens_clothing_category_data = {
        "name": "Men'sclothing",
        "description": "Clothing for men",
        "parent": clothing_category_id,
    }
    mens_clothing_response = client.post(
        reverse("products:categories-list"),
        mens_clothing_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response in conftest after creating 'Men's Clothing' category: {mens_clothing_response.data} status {mens_clothing_response.status_code}")
    if mens_clothing_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Men's Clothing' category: {mens_clothing_response.data}")
        pytest.fail("Category 'Men\'s Clothing' creation failed in fixture")
    mens_clothing_category_id = mens_clothing_response.data["id"]

    # Women's Clothing
    womens_clothing_category_data = {
        "name": "Women'sclothing",
        "description": "Clothing for women",
        "parent": clothing_category_id,
    }
    womens_clothing_response = client.post(
        reverse("products:categories-list"),
        womens_clothing_category_data,
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"Response in conftest after creating 'Women's Clothing' category: {womens_clothing_response.data} status {womens_clothing_response.status_code}")
    if womens_clothing_response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating 'Women's Clothing' category: {womens_clothing_response.data}")
        pytest.fail("Category 'Women\'s Clothing' creation failed in fixture")
    womens_clothing_category_id = womens_clothing_response.data["id"]

    #
    return {
        "client": client,
        "token": token,
        "shoe_top_level_category_id": shoes_category_id,
        "clothing_top_level_category_id": clothing_category_id,
        "mens_id": mens_shoe_category_id,
        "womens_id": womens_shoe_category_id,
        "womenboots_id": womenboots_shoe_category_id,
        "mens_clothing_id": mens_clothing_category_id,
        "womens_clothing_id": womens_clothing_category_id,
    }

@pytest.fixture()
def setup_brand(setup_users):
    """
Fixture to set up a brand for testing.
(No changes needed for brand fixture)
"""
    client = setup_users["client"]
    inventory_m_token = setup_users["inventory_manager_token"]

    # Create a brand
    brand_data = {
        "name": "Nike",
        "description": "Nike shoes",
    }

    response = client.post(reverse("products:brands-list"),
                           brand_data,
                           HTTP_AUTHORIZATION=f"Token {inventory_m_token}"
                           )
    print(f"Response in conftest after brand creation: {response.data} status {response.status_code}")
    if response.status_code != status.HTTP_201_CREATED:
        print(f"Error creating brand: {response.data}")
        pytest.fail("Brand creation failed in fixture")

    return {
        "client": client,
        "token": inventory_m_token,
        "brand_id": response.data["id"],
    }

from django.http import QueryDict

@pytest.fixture()
def setup_products(setup_users, setup_category, setup_brand):
    """
    Fixture to set up ShoeProduct and ClothingProduct using separate requests
    per category. Returns a dictionary containing lists of product IDs for each type.
    """
    client = setup_users["client"]
    brand_id = setup_brand["brand_id"]
    inventory_m_token = setup_users["inventory_manager_token"]
    mens_id = setup_category["mens_id"]
    womens_id = setup_category["womens_id"]
    womenscloth_id = setup_category["womens_clothing_id"]

    shoe_data_list = [
        {
            "name": "Running Shoe Mens Bulk",
            "description": "Men's shoe for bulk running",
            "brand": brand_id,
            "category": mens_id,
            "stock": 25,
            "price": 99.99,
            "gender": "mens",
            "material": "leather",
            "size_type": "US",
            "style": "Casual",
            "sizes": [
                {"size": "42"},
                {"size": "43"}
            ],
            "colors": [
                {"color": "red"},
                {"color": "blue"}
            ],
            "variants": [
                {"size": "42", "color": "red", "stock": 10},
                {"size": "43", "color": "blue", "stock": 15}
            ]
        },
        {
            "name": "Another Running Shoe Mens Bulk",
            "description": "Another men's shoe for running in bulk",
            "brand": brand_id,
            "category": mens_id, # Same mens_id for shoes
            "stock": 20,
            "price": 120.00,
            "gender": "mens",
            "material": "synthetic",
            "size_type": "US",
            "style": "Sporty",
            "sizes": [
                {"size": "41"},
                {"size": "42"}
            ],
            "colors": [
                {"color": "black"},
                {"color": "white"}
            ],
            "variants": [
                {"size": "41", "color": "black", "stock": 8},
                {"size": "42", "color": "white", "stock": 12}
            ]
        },
    ]

    clothing_data_list = [
        {
            "name": "TShirt Womens Bulk",
            "description": "Womens t-shirt for casual wear in bulk",
            "brand": brand_id,
            "category": womenscloth_id,
            "stock": 50,
            "price": 24.99,
            "material": "cotton",
            "color": "white",
            "variants": [
                {"size": "S", "stock": 20},
                {"size": "M", "stock": 30}
            ]
        },
        {
            "name": "Jeans Womens Bulk",
            "description": "Womens jeans for everyday wear in bulk",
            "brand": brand_id,
            "category": womenscloth_id,
            "price": 59.50,
            "material": "denim",
            "color": "blue",
            "variants": [
                {"size": "S", "stock": 15},
                {"size": "M", "stock": 25}
            ]
        },
    ]

    shoe_url = reverse("products:products-list")
    shoe_query_params = QueryDict(mutable=True)
    shoe_query_params['category'] = mens_id # Category for shoes
    shoe_url_with_params = shoe_url + "?" + shoe_query_params.urlencode()

    clothing_url = reverse("products:products-list") # Same URL endpoint
    clothing_query_params = QueryDict(mutable=True)
    clothing_query_params['category'] = womenscloth_id # Category for clothing
    clothing_url_with_params = clothing_url + "?" + clothing_query_params.urlencode()


    # --- Make Separate POST requests ---
    shoe_response = client.post(
        shoe_url_with_params,
        shoe_data_list,
        HTTP_AUTHORIZATION=f"Token {inventory_m_token}",
        format="json",
    )

    clothing_response = client.post(
        clothing_url_with_params,
        clothing_data_list,
        HTTP_AUTHORIZATION=f"Token {inventory_m_token}",
        format="json",
    )

    print(f"Shoe Create Response in conftest: {shoe_response.data}")
    print(f"Clothing Create Response in conftest: {clothing_response.data}")

    assert shoe_response.status_code == status.HTTP_201_CREATED
    assert isinstance(shoe_response.data, list)
    assert len(shoe_response.data) == len(shoe_data_list)

    assert clothing_response.status_code == status.HTTP_201_CREATED
    assert isinstance(clothing_response.data, list)
    assert len(clothing_response.data) == len(clothing_data_list)

    shoe_product_ids = [product_response['id'] for product_response in shoe_response.data]
    clothing_product_ids = [product_response['id'] for product_response in clothing_response.data]
    
    return {
        "shoe_product_ids": shoe_product_ids, # Return separate lists of IDs
        "clothing_product_ids": clothing_product_ids,
        "all_product_ids": [shoe_product_ids, clothing_product_ids] # Still return combined for convenience if needed
    }