from django.db import models
from django.contrib.auth.models import User
import uuid


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


def generate_order_id():
    return f"GGO-{uuid.uuid4().hex[:8].upper()}"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=20, unique=True, default=generate_order_id)

    # Financial details - merged and cleaned
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='Pending')

    # Delivery details - added null=True to match view logic
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    directions = models.TextField(blank=True, null=True)
    preferred_time = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Gas details
    size = models.CharField(max_length=10)
    brand = models.CharField(max_length=50, blank=True, null=True)
    exchange = models.CharField(max_length=10, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    # Location tracking
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)
    rider_latitude = models.FloatField(null=True, blank=True)
    rider_longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id} - {self.phone}"

class USSDOrder(models.Model):
    session_id = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    gas_size = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.gas_size} x {self.quantity}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profile_pics',
        default='profile_pics/default.png',  
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username
