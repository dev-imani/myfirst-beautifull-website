import pytest
from django.urls import reverse
from rest_framework import status
from products.choices import CategoryChoices
from products.models import Brand, Category

@pytest.mark.django_db
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
    category_id = setup_category["shoe_top_level_category_id"]

    url = reverse("products:categories-detail", kwargs={"pk": category_id})

    response = client.get(
        url,
        HTTP_AUTHORIZATION=f"Token {token}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == category_id #add assertion for the id

@pytest.mark.django_db
class TestCategory:
    """Test suite for the shoe shop category API views."""
    @pytest.fixture(autouse=True)
    def setup(self, setup_users, setup_category):
        "set up daata for tests" 
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
    pytest.mark.parametrize(
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
        assert response.status_code == expected_status

   
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
 
    @pytest.mark.parametrize(
        "get_endpoint, category_id, token, expected_status",
        [
            #store user can't update a category
            (
                "categories-detail",
                "top_level_category_id",
                "store_user_token",
                status.HTTP_403_FORBIDDEN,
            ),

             # Store Owner can update a category
            (
                "categories-detail",
                "womens_shoe_category_id",
                "store_owner_token",
                status.HTTP_200_OK,
            ),

            # Store Owner can't update toplevelcategory except description field
            (
                "categories-detail",
                "top_level_category_id",
                "store_owner_token",
                status.HTTP_400_BAD_REQUEST,
            ),
            #inventory manager can update a category 
            (
                "categories-detail",
                "womens_boot_category_id",
                "inventory_manager_token",
                status.HTTP_200_OK,
            ),
        ],
    )
    def test_update_category(self, get_endpoint, category_id, token, expected_status):
        """Test retrieving a category."""
        category_id = getattr(self, category_id)
        token = getattr(self, token)
        update_data = {
            "name": "updatedname",
            "status": "inactive",
            "parent": self.mens_shoe_category_id
        }

        response = self.client.patch(
            reverse(f"products:{get_endpoint}", kwargs={"pk": category_id}),
            update_data,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        print(f"response after update: {response.data}")
        assert response.status_code == expected_status
    @pytest.mark.parametrize(
        "get_endpoint, category_id, token, expected_status",
        [
            # Store User can't delete a category
            (
                "categories-detail",
                "mens_shoe_category_id",
                "store_user_token",
                status.HTTP_403_FORBIDDEN
            ),

            # Store Owner can delete a category
            (
                "categories-detail", 
                "top_level_category_id",
                "store_owner_token",
                status.HTTP_204_NO_CONTENT),
     
         
            #inventory manager can delete a category 
            (
                "categories-detail",
                "womens_boot_category_id",
                "inventory_manager_token",
                status.HTTP_204_NO_CONTENT,
            ),
        ],
    )
    def test_delete_category(self, get_endpoint, category_id, token, expected_status):
        """Test deleting a category."""
        category_id = getattr(self, category_id)
        token = getattr(self, token)
    
        response = self.client.delete(
            reverse(f"products:{get_endpoint}", kwargs={"pk": category_id}),
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        print(f"response after delete: {response.data}")
        assert response.status_code == expected_status
        # If deleted successfully, verify it's removed from the database
        if expected_status == status.HTTP_204_NO_CONTENT:
            assert not Category.objects.filter(pk=category_id).exists()

        if category_id == self.top_level_category_id:
            assert not Category.objects.filter(pk=self.top_level_category_id).exists()
            assert not Category.objects.filter(pk=self.mens_shoe_category_id).exists()
    
    @pytest.mark.parametrize("depth, expected_depth", [
    (0, 1),  # ✅ Returntop-level
    (1, 1),  # ✅ Return 1 level
    (2, 2),  # ✅ Return 2 levels if available
    (5, 5),  # ✅ returns 5 if available
    (10, 5), # ✅ Requested 10, but only 5 canexist
    ])
    def test_category_hierarchy_limited_by_actual_depth(self, depth, expected_depth):
        """Test that hierarchy returns only available depth, not exceeding existing levels."""
        url = reverse("products:categories-hierarchy") + f"?depth={depth}"

        response = self.client.get(url, HTTP_AUTHORIZATION=f"Token {self.store_owner_token}")
        print(f"response after get: {response.data}")
        assert response.status_code == 200
        assert len(response.data) <= expected_depth  # Ensures max returned depth is within range


@pytest.mark.django_db
class TestBrand:
    """Test suite for the shoe shop brand API views."""

    @pytest.fixture(autouse=True)
    def setup(self, setup_users, setup_brand):
        """Set up data for tests."""
        self.client = setup_users["client"]
        self.store_user_token = setup_users["store_user_token"]
        self.store_owner_token = setup_users["store_owner_token"]
        self.store_manager_token = setup_users["store_manager_token"]
        self.inventory_manager_token = setup_users["inventory_manager_token"]
        self.sales_associate_token = setup_users["sales_associate_token"]
        self.customer_service_token = setup_users["customer_service_token"]
        self.brand_id = setup_brand["brand_id"]

    @pytest.mark.parametrize(
        "url, token, expected_status",
        [
            # Store Owner can get all brands
            ("brands-list", "store_owner_token", status.HTTP_200_OK),
            # Store Manager can get all brands
            ("brands-list", "store_manager_token", status.HTTP_200_OK),
            # Inventory Manager can get all brands
            ("brands-list", "inventory_manager_token", status.HTTP_200_OK),
            # Sales Associate can get all brands
            ("brands-list", "sales_associate_token", status.HTTP_200_OK),
            # Customer Service can get all brands
            ("brands-list", "customer_service_token", status.HTTP_200_OK),
            #user can get brands
            ("brands-list", "store_user_token", status.HTTP_200_OK),
        ],
    )
    def test_get_brands(self, url, token, expected_status):
        """Test retrieving brands."""
        token = getattr(self, token)
        response = self.client.get(
            reverse(f"products:{url}"),
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        print(f"Response data: {response.data}")
        assert response.status_code == expected_status
    
    @pytest.mark.parametrize(
        "url, token, brand_id,  expected_status",
        [
            # Store Owner can update brands
            ("brands-detail", "store_owner_token", "brand_id", status.HTTP_200_OK),
            # Store Manager can update brands
            ("brands-detail", "store_manager_token", "brand_id", status.HTTP_200_OK),
            # Inventory Manager can update brands
            ("brands-detail", "inventory_manager_token", "brand_id", status.HTTP_200_OK),
            # Sales Associate can't update brands
            ("brands-detail", "sales_associate_token", "brand_id", status.HTTP_403_FORBIDDEN),
            # Customer Service can't update brands
            ("brands-detail", "customer_service_token", "brand_id", status.HTTP_403_FORBIDDEN),
            #user can't delete brands
            ("brands-detail", "store_user_token", "brand_id", status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_update_brand(self, url, token, brand_id, expected_status):
        """Test updating brands."""
        token = getattr(self, token)
        brandid = getattr(self, brand_id)
        data = {
            "name": "updatedname",
        }
        response = self.client.patch(
            reverse(f"products:{url}", kwargs={"pk": brandid}),
            data,
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        print(f"Response data: {response.data}")
        assert response.status_code == expected_status
    
    @pytest.mark.parametrize(
        "url, token, brand_id,  expected_status",
        [
            # Store Owner can delete brands
            ("brands-detail", "store_owner_token", "brand_id", status.HTTP_204_NO_CONTENT),
            # Store Manager can delete brands
            ("brands-detail", "store_manager_token", "brand_id", status.HTTP_204_NO_CONTENT),
            # Inventory Manager can delete brands
            ("brands-detail", "inventory_manager_token", "brand_id", status.HTTP_204_NO_CONTENT),
            # Sales Associate can't delete brands
            ("brands-detail", "sales_associate_token", "brand_id", status.HTTP_403_FORBIDDEN),
            # Customer Service can't delete brands
            ("brands-detail", "customer_service_token", "brand_id", status.HTTP_403_FORBIDDEN),
            #user can't delete brands
            ("brands-detail", "store_user_token", "brand_id", status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_delete_brand(self, url, token, brand_id, expected_status):
        """Test deleting brands."""
        token = getattr(self, token)
        brandid = getattr(self, brand_id)
        response = self.client.delete(
            reverse(f"products:{url}", kwargs={"pk": brandid}),
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        print(f"Response data: {response.data}")
        assert response.status_code == expected_status
        # If deleted successfully, verify it's removed from the database
        if expected_status == status.HTTP_200_OK:
            assert not Brand.objects.filter(pk=brandid).exists() # pylint: disable=no-member