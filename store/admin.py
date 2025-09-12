from django.contrib import admin
from .models import Product, ProductGallery, Variation, VariationCategory
import admin_thumbnails
# Register your models here.

class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1
    
@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'slug', 'product_price', 'stock', 'is_available', 'category', 'created_date', 'modified_date')
    prepopulated_fields = {'slug': ('product_name',)}
    list_filter = ('category', 'is_available')
    search_fields = ('product_name', 'description')
    inlines = [VariationInline, ProductGalleryInline]

admin.site.register(Product, ProductAdmin)
admin.site.register(Variation)
admin.site.register(VariationCategory)
admin.site.register(ProductGallery)