from products.models import ClothingProduct, ShoeProduct
from products.serializers import ClothingProductSerializer, ShoeProductSerializer


class ProductMapper:

    CATEGORY_TO_SERIALIZER = {

        'shoes': ShoeProductSerializer,

        'clothing': ClothingProductSerializer,

    }


    @classmethod

    def get_serializer_for_category(cls, category):

        root_category = category.get_root().name.lower()

        return cls.CATEGORY_TO_SERIALIZER.get(root_category)


    @classmethod

    def get_model_for_category(cls, category):

        root_category = category.get_root().name.lower()

        if root_category == 'shoes':

            return ShoeProduct

        elif root_category == 'clothing':

            return ClothingProduct

        return None 