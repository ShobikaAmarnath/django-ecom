from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib import messages

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from .models import Product, ProductGallery, Variation
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from wishlist.models import Wishlist, WishlistItem
from wishlist.views import _wishlist_id

def store(request, category_slug=None):
    """
    Handles the store page, product filtering, and pagination.
    """
    # 1. Get initial set of products based on category
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)

    # 2. Build a list of all possible filters from the variations
    available_filters = {}
    variation_values = Variation.objects.filter(product__in=products).values_list('category__name', 'value').distinct()
    for category_name, value in variation_values:
        cat_name_lower = category_name.lower()
        if cat_name_lower not in available_filters:
            available_filters[cat_name_lower] = []
        if value not in available_filters[cat_name_lower]:
            available_filters[cat_name_lower].append(value)

    # 3. Apply active filters from the request URL
    query_params = request.GET.copy()
    
    # Apply variation filters (e.g., color, size)
    for category_name, values in query_params.lists():
        if category_name in available_filters and values:
            products = products.filter(
                variation__category__name__iexact=category_name, 
                variation__value__in=values
            )

    # Apply price filters
    if min_price := query_params.get('min_price'):
        products = products.filter(product_price__gte=min_price)
    if max_price := query_params.get('max_price'):
        products = products.filter(product_price__lte=max_price)

    # Ensure unique products after filtering across related tables
    products = products.distinct().order_by('id')

    # 4. Paginate the FINAL filtered queryset
    paginator = Paginator(products, 3)  # Showing 6 products per page
    page_number = request.GET.get('page')
    paged_products = paginator.get_page(page_number)

    # 5. Get wishlist product IDs for the current user
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True))
    else:
        try:
            wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
            wishlist_ids = list(WishlistItem.objects.filter(wishlist=wishlist).values_list('product_id', flat=True))
        except Wishlist.DoesNotExist:
            pass # No session wishlist exists yet

    # 6. Prepare context for the template
    # KEY FIX: Remove 'page' from the query parameters before encoding
    if 'page' in query_params:
        del query_params['page']

    processed_filters = {}
    for category_name, available_values in available_filters.items():
        selected_values = request.GET.getlist(category_name)
        options = []
        for value in available_values:
            options.append({
                'value': value,
                'is_selected': value in selected_values
            })
        processed_filters[category_name] = options

    context = {
        'products': paged_products,
        'product_count': products.count(),
        'wishlist_products': wishlist_ids,
        'available_filters': available_filters,
        'selected_filters': request.GET, # Useful for checking which filters are active
        'query_params': query_params.urlencode(), # PASS THE ENCODED FILTERS HERE
        'processed_filters': processed_filters,
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
