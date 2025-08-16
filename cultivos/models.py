from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('category', 'name')
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class Municipality(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'
        ordering = ['name']

    def __str__(self):
        return self.name

class Sowing(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'En curso'),
        ('harvested', 'Cosechado'),
        ('failed', 'Fallido'),
    )
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sowings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sowings')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text='Cantidad (ha o ton)')
    sowing_date = models.DateField()
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='sowings')
    harvest_date = models.DateField(null=True, blank=True)
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
