from django.db import models
from category.models import Category

# Create your models here.

class Product(models.Model):
    product_name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        from django.urls import reverse
        return reverse('product_detail', args=[self.category.slug, self.slug])
    
    def __str__(self):
        return self.product_name
    
class VariationCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. Color, Size, Storage
    
    class Meta:
        verbose_name = 'VariationCategory'
        verbose_name_plural = 'variation_categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variations")
    category = models.ForeignKey(VariationCategory, on_delete=models.CASCADE, related_name="variations")
    value = models.CharField(max_length=100)  # e.g. Red, XL, 128GB
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name}: {self.value}"

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to='store/products', max_length=255)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ProductGallery'
        verbose_name_plural = 'product_gallery'

    def __str__(self):
        return self.product.product_name