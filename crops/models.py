from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    
    min_temp = models.FloatField(null=True, blank=True)
    max_temp = models.FloatField(null=True, blank=True)
    min_rain = models.FloatField(null=True, blank=True)
    max_rain = models.FloatField(null=True, blank=True)
    min_humidity = models.FloatField(null=True, blank=True)
    max_humidity = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ('category', 'name')
        ordering = ['category__name', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.category.name})"

class Municipality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Sowing(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'En curso'),
        ('harvested', 'Cosechado'),
        ('failed', 'Fallido'),
    )
    UNIT_CHOICES = [
    ('ha', 'Hectáreas'),
    ('ton', 'Toneladas'),
    ('m2', 'Metros cuadrados'),
    ('plantas', 'Número de plantas'),
]

    unit = models.CharField(
    max_length=20,
    choices=UNIT_CHOICES,
    default='ha',
    help_text='Unidad de medida'
)
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sowings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sowings')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    sowing_date = models.DateField()
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='sowings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sowing_date']),
            models.Index(fields=['status']),
            models.Index(fields=['municipality']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.quantity} - {self.farmer.username}"


class Crop(models.Model):
    name = models.CharField(max_length=100)
    min_temp = models.FloatField(null=True, blank=True)
    max_temp = models.FloatField(null=True, blank=True)
    min_rain = models.FloatField(null=True, blank=True)
    max_rain = models.FloatField(null=True, blank=True)
    min_humidity = models.FloatField(null=True, blank=True)
    max_humidity = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name