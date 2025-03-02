from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from mptt.models import MPTTModel, TreeForeignKey
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

User = get_user_model()

class Region(MPTTModel):
    """
    Hierarchical regions using MPTT.
    Examples:
    - Country
    └── County
        └── Sub-county
            └── Town
    """
    name = models.CharField(max_length=100)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    class MPTTMeta:
        order_insertion_by = ['name']
        
    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Regions"

class PickupStation(models.Model): 
    """
    Model for pickup locations where customers can collect their orders
    """
    name = models.CharField(max_length=255)
    region = TreeForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='stations'
    )
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    operating_hours = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.region}" if self.region else self.name
        
    class Meta:
        verbose_name = "Pickup Station"
        verbose_name_plural = "Pickup Stations"
        ordering = ['name']

class Address(models.Model):
    """
    A generic address model supporting both geolocation and manual entry
    """
    ADDRESS_TYPE_CHOICES = [
        ('shipping', _('Shipping')),
        ('billing', _('Billing')),
        ('both', _('Both')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='both')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='Kenya')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    is_manual = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    region = TreeForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='addresses')

    def __str__(self):
        return f"{self.full_name} | {self.city} | {self.country}" if not self.is_manual else f"Manual: {self.latitude}/{self.longitude}"
    
    @classmethod
    def get_default_shipping_address(cls, user):
        if not user.is_authenticated:
            return None
        return user.addresses.filter(is_default=True, address_type__in=['shipping', 'both']).first()

    @classmethod
    def get_default_billing_address(cls, user):
        if not user.is_authenticated:
            return None
        return user.addresses.filter(is_default=True, address_type__in=['billing', 'both']).first()

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set other addresses of the same type to not default
            qs = Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk)
            qs.update(is_default=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-updated_at']

class DeliveryOption(models.Model):
    """
    Represents the delivery choice made by the customer for an order
    """
    DELIVERY_TYPE_CHOICES = [
        ('home', _('Home Delivery')),
        ('pickup', _('Pickup Station')),
    ]
    
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='delivery_option')
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPE_CHOICES)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    pickup_station = models.ForeignKey(PickupStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    delivery_instructions = models.TextField(blank=True, help_text="Special instructions for delivery")
    preferred_delivery_date = models.DateField(null=True, blank=True)
    preferred_delivery_time = models.CharField(max_length=50, blank=True, help_text="Preferred time of day for delivery")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_delivery_type_display()} for {self.order}"
    
    def clean(self):
        if self.delivery_type == 'home' and not self.address:
            raise ValidationError({"address": _("Home delivery requires a valid address")})
        if self.delivery_type == 'pickup' and not self.pickup_station:
            raise ValidationError({"pickup_station": _("Pickup delivery requires a valid station")})

    class Meta:
        verbose_name = "Delivery Option"
        verbose_name_plural = "Delivery Options"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('ready_for_pickup', _('Ready for Pickup')),
        ('delivered', _('Delivered')),
        ('collected', _('Collected')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )

    PAYMENT_STATUS_CHOICES = (
        ('awaiting', _('Awaiting Payment')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partially_refunded', _('Partially Refunded')),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('card', _('Credit/Debit Card')),
        ('mpesa', _('M-Pesa')),
        ('paypal', _('PayPal')),
        ('bank', _('Bank Transfer')),
        ('cash', _('Cash on Delivery')),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_email = models.EmailField(null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='awaiting')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    region = TreeForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def generate_order_number(self):
        return str(uuid.uuid4()).split('-')[0].upper()

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
            
        # Update status based on delivery type if applicable
        try:
            if self.delivery_option and self.status == 'shipped':
                if self.delivery_option.delivery_type == 'pickup':
                    self.status = 'ready_for_pickup'
        except DeliveryOption.DoesNotExist:
            pass
            
        super().save(*args, **kwargs)

    def calculate_total(self):
        self.subtotal = sum(item.get_total() for item in self.items.all())
        self.total = self.subtotal + self.shipping_cost + self.tax - self.discount
        return self.total
        
    def get_delivery_address(self):
        """Get the delivery address depending on the delivery option"""
        try:
            if hasattr(self, 'delivery_option'):
                if self.delivery_option.delivery_type == 'home':
                    return self.delivery_option.address
        except Exception:
            pass
        return None
        
    def get_pickup_station(self):
        """Get the pickup station if applicable"""
        try:
            if hasattr(self, 'delivery_option') and self.delivery_option.delivery_type == 'pickup':
                return self.delivery_option.pickup_station
        except Exception:
            pass
        return None

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    item_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    item_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    options = models.JSONField(null=True, blank=True, help_text="Store product options like size, color, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    def get_total(self):
        return (self.product_price * self.quantity) - self.item_discount + self.item_tax

class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order histories'

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"

class Payment(models.Model):
    """
    Records all payment attempts and successful payments for orders
    """
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partial_refund', _('Partially Refunded')),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=Order.PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(null=True, blank=True)
    is_refund = models.BooleanField(default=False)
    refund_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.amount} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']

class Coupon(models.Model):
    """
    Coupons and discount codes
    """
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
        ('free_shipping', _('Free Shipping')),
    )
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    current_uses = models.PositiveIntegerField(default=0)
    regions = models.ManyToManyField(Region, blank=True, related_name='coupons', help_text="Restrict coupon to specific regions")
    
    def __str__(self):
        return self.code
        
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.max_uses == 0 or self.current_uses < self.max_uses)
        )

class OrderCoupon(models.Model):
    """
    Tracks coupons applied to orders
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='applied_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, related_name='orders')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.coupon.code}"

class ShippingRate(models.Model):
    """
    Shipping rates based on regions and delivery methods
    """
    DELIVERY_TYPE_CHOICES = [
        ('home', _('Home Delivery')),
        ('pickup', _('Pickup Station')),
        ('both', _('Both')),
    ]
    
    name = models.CharField(max_length=100)
    region = TreeForeignKey(
        Region, 
        on_delete=models.CASCADE, 
        related_name='shipping_rates'
    )
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPE_CHOICES, default='both')
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    additional_rate_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_delivery_days = models.PositiveIntegerField(default=1)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Order value for free shipping (0 = no free shipping)")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.region.name} ({self.get_delivery_type_display()}: ${self.base_rate})"
        
    class Meta:
        unique_together = ('region', 'delivery_type')