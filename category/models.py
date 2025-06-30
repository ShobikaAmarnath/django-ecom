from django.db import models

# Create your models here.

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True, null=True)
    category_image = models.ImageField(upload_to='photos/categories', blank=True, null=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['category_name']

    def get_url(self):
        from django.urls import reverse
        return reverse('products_by_category', args=[self.slug])
    
    def __str__(self):
        return self.category_name