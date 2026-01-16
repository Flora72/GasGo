from django.contrib import admin
from .models import Vendor, Order, USSDOrder, Profile

# Register your models here.
admin.site.register(Vendor)
admin.site.register(Order)
admin.site.register(USSDOrder)
admin.site.register(Profile)