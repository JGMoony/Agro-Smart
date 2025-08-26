from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100)
    
    min_temp = models.FloatField(null=True, blank=True)
    max_temp = models.FloatField(null=True, blank=True)
    min_rain = models.FloatField(null=True, blank=True)
    max_rain = models.FloatField(null=True, blank=True)
    min_humidity = models.FloatField(null=True, blank=True)
    max_humidity = models.FloatField(null=True, blank=True)
    min_altitude = models.IntegerField(null=True, blank=True)
    max_altitude = models.IntegerField(null=True, blank=True)
    
    cycle_days = models.IntegerField(null=True, blank=True, help_text="Días aproximados para cosecha")
    cost_per_hectare = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    yield_per_hectare = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
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
    ('hectarea', 'Hectárea'),
]

    unit = models.CharField(
    max_length=20,
    choices=UNIT_CHOICES,
    help_text='Unidad de medida'
)
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sowings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sowings')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    sowing_date = models.DateField()
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='sowings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)

    area = models.FloatField(default=1.0)
    area_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='hectarea')
    estimated_harvest_date = models.DateField(null=True, blank=True)
    expected_harvest_date = models.DateField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
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

class Prices(models.Model):
    UNIT_CHOICES = [
        ('k', 'kilo'),
        ('t', 'tonelada'),
        ('a', 'arroba')
    ]
    value = models.DecimalField(decimal_places=2,max_digits=10)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        help_text='Unidad de medida'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return f"{self.date} - {self.value} {self.unit} ({self.date.strftime('%d/%m/%Y')})"