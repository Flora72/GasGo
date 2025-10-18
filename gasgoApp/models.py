from django.db import models
from django.contrib.auth.models import User
import uuid


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    location_lat = models.FloatField()
    location_lng = models.FloatField()

    def __str__(self):
        return self.name

def generate_order_id():
    return f"GGO-{uuid.uuid4().hex[:8].upper()}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)
    order_id = models.CharField(max_length=20, unique=True, default=generate_order_id)
    status = models.CharField(max_length=20, default='Pending')

    # Delivery details
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    directions = models.TextField(blank=True)
    preferred_time = models.CharField(max_length=50)
    notes = models.TextField(blank=True)

    # Gas details
    size = models.CharField(max_length=10)
    brand = models.CharField(max_length=50, blank=True)
    exchange = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField(default=1)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 


    # Location tracking
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)
    rider_latitude = models.FloatField(null=True, blank=True)
    rider_longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id} - {self.user.username}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profile_pics',
        default='default.png',
        blank=True, 
        null=True
    )
