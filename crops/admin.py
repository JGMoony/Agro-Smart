from django.contrib import admin
from .models import Category, Product, Municipality, Sowing

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Municipality)
admin.site.register(Sowing)

class CropParameterAdmin(admin.ModelAdmin):
    list_display = ('product', 'temp_min', 'temp_max', 'hum_min', 'hum_max', 'rain_min', 'rain_max', 'wind_max')
    search_fields = ('product__name',)