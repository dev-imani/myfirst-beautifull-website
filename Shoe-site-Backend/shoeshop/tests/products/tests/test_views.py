import pytest
from django.urls import reverse
from rest_framework import status
from products.choices import CategoryChoices

'''@pytest.mark.django_db
def test_root_category_creation(setup_category):
    """
    Test that a store owner can create a root category.
    """
    client = setup_category["client"]
    token = setup_category["token"]

    url = reverse("products:categories-list")
    data = {
        "description": "All types of clothing ",
        "top_level_category": CategoryChoices.CLOTHING, 
    }

    response = client.post(
        url,
        data, #send data directly
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"response status after creation :  {response.data} status : {response.status_code}")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Clothing"
    assert response.data["description"] == "All types of clothing"
    assert response.data["parent"] is None


@pytest.mark.django_db
def test_get_category(setup_category):
    """
    Test that a store owner can get category details.
    """
    client = setup_category["client"]
    token = setup_category["token"]
    category_id = setup_category["top_level_category_id"]

    url = reverse("products:categories-detail", kwargs={"pk": category_id})

    response = client.get(
        url,
        HTTP_AUTHORIZATION=f"Token {token}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == category_id #add assertion for the id
'''
@pytest.mark.django_db
class TestCategory:
    """Test suite for the shoe shop category API views."""
    @pytest.fixture(autouse=True)
    def setup(self, setup_users, setup_category):
        self.client = setup_users["client"]
        self.store_user_token = setup_users["store_user_token"]
        self.store_owner_token = setup_users["store_owner_token"]
        self.store_manager_token = setup_users["store_manager_token"]
        
        self.inventory_manager_token = setup_users["inventory_manager_token"]
        
        self.sales_associate_token = setup_users["sales_associate_token"]

        self.customer_service_token = setup_users["customer_service_token"]
        
        self.top_level_category_id = setup_category["shoe_top_level_category_id"]
        self.mens_shoe_category_id = setup_category["mens_id"]
        self.womens_shoe_category_id = setup_category["womens_id"]
        self.womens_boot_category_id = setup_category["womenboots_id"]
    '''@pytest.mark.parametrize(
        "get_endpoint, token, expected_status",
        [
            # Store Owner can get all categories
            (
                "categories-list",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            # Store Manager can get all categories
            (
                "categories-list",
                "store_manager_token",
                status.HTTP_200_OK,
            ),
            # Inventory Manager can get all categories
            (
                "categories-list",
                "inventory_manager_token",
                status.HTTP_200_OK,
            ),
            # Sales Associate can get all categories
            (
                "categories-list",
                "sales_associate_token",
                status.HTTP_200_OK,
            ),
            # Customer Service can get all categories
            (
                "categories-list",
                "customer_service_token",
                status.HTTP_200_OK,
            ),
        ],
    )
    def test_get_categories(self, get_endpoint, token, expected_status):
        """Test retrieving categories."""
        token = getattr(self, token)
        response = self.client.get(
            reverse(f"products:{get_endpoint}"),
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        print(f"Response data: {response.data}")
        assert response.status_code == expected_status'''

   
    @pytest.mark.parametrize(
        "get_endpoint, category_id, token, expected_status",
        [
            #store user can get a category
            (
                "categories-detail",
                "top_level_category_id",
                "store_user_token",
                status.HTTP_200_OK,
            ),
            # Store Owner can get a category
            (
                "categories-detail",
                "top_level_category_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),
            # Store Manager can get a category
            (
                "categories-detail",
                "mens_shoe_category_id",
                "store_manager_token",
                status.HTTP_200_OK,
            ),
            # Inventory Manager can get a category
            (
                "categories-detail",
                "womens_shoe_category_id",
                "inventory_manager_token",
                status.HTTP_200_OK,
            ),
            # Sales Associate can get a category
            (
                "categories-detail",
                "womens_boot_category_id",
                "sales_associate_token",
                status.HTTP_200_OK,
            ),
            # Customer Service can get a category
            (
                "categories-detail",
                "womens_boot_category_id",
                "customer_service_token",
                status.HTTP_200_OK,
            ),
        ],
    )
    def test_get_category(self, get_endpoint, category_id, token, expected_status):
        """Test retrieving a category."""
        category_id = getattr(self, category_id)
        token = getattr(self, token)
        response = self.client.get(
            reverse(f"products:{get_endpoint}", kwargs={"pk": category_id}),
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        print(f"Response data: {response.data}")
        assert response.status_code == expected_status
 