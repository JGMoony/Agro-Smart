from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User
admin.site.register(User)

from cultivos.models import Category, Product, Municipality, Sowing
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Municipality)
admin.site.register(Sowing)