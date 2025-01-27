import pytest
from django.urls import reverse
from rest_framework import status

from products.choices import CategoryChoices

@pytest.mark.django_db
def test_root_category_creation(setup_category):
    """
    Test that a store owner can create a root category.
    """
    client = setup_category["client"]
    token = setup_category["token"]

    url = reverse("products:categories-list")
    data = {
        "name": "AnotherShoes",
        "description": "All types of shoes",
        "top_level_category": CategoryChoices.SHOES, 
    }

    response = client.post(
        url,
        data, #send data directly
        HTTP_AUTHORIZATION=f"Token {token}"
    )
    print(f"response status after creation :  {response.data}")
    '''assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "AnotherShoes"
    assert response.data["description"] == "All types of shoes"
    assert response.data["parent"] is None


@pytest.mark.django_db
def test_get_category(setup_category):
    client = setup_category["client"]
    token = setup_category["token"]
    category_id = setup_category["category_id"]

    url = reverse("products:categories-detail", kwargs={"pk": category_id})

    response = client.get(
        url,
        HTTP_AUTHORIZATION=f"Token {token}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == category_id #add assertion for the id

   
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "AnotherShoes"
    assert response.data["description"] == "All types of shoes"
    assert response.data["parent"] is None'''
   