# users/choices.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class SexChoices(models.TextChoices):
    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')
    OTHER = 'OTHER', _('Other')

class UserRoles(models.TextChoices):
    STORE_OWNER = 'STORE_OWNER', _('Store Owner')
    STORE_MANAGER = 'STORE_MANAGER', _('Store Manager')
    INVENTORY_MANAGER = 'INVENTORY_MANAGER', _('Inventory Manager')
    SALES_ASSOCIATE = 'SALES_ASSOCIATE', _('Sales Associate')
    CUSTOMER_SERVICE = 'CUSTOMER_SERVICE', _('Customer Service')
    CASHIER = 'CASHIER', _('Cashier')
