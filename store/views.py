from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib import messages

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from .models import Product, ProductGallery
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

# Create your views here.

from wishlist.models import Wishlist, WishlistItem
from wishlist.views import _wishlist_id


def store(request, category_slug=None):
    categories = None
    products = None
    if category_slug is not None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True).order_by('id')
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.filter(is_available=True).order_by('id')
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        try:
            paged_products = paginator.get_page(page)
        except PageNotAnInteger:
            paged_products = paginator.page(1)
        except EmptyPage:
            paged_products = paginator.page(paginator.num_pages)
        product_count = products.count()

    # ✅ Wishlist integration
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_items = WishlistItem.objects.filter(user=request.user, is_active=True)
    else:
        wishlist_obj, _ = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist_obj, is_active=True)

    wishlist_ids = list(wishlist_items.values_list('product_id', flat=True))

    context = {
        'products': paged_products,
        'product_count': product_count,
        'wishlist_products': wishlist_ids,   
    }
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
        
        # Get variations grouped by category
        variations_by_category = {}
        for variation in single_product.variations.filter(is_active=True):
            category = variation.category.name
            if category not in variations_by_category:
                variations_by_category[category] = []
            variations_by_category[category].append(variation.value)

    except Product.DoesNotExist:
        raise Http404("Product not found")
    
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'variations_by_category': variations_by_category,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    products = None
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword: 
            print(f"Searching for: {keyword}")
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            print(f"Found {products.count()} products matching '{keyword}'")
            product_count = products.count()
    
    context = {
        'products': products,
        'product_count': product_count if products else 0,
    }
    return render(request, 'store/store.html', context)
