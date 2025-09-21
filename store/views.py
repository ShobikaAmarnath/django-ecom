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
    category = None
    
    # 1. Start with a base queryset of all available products
    products = Product.objects.filter(is_available=True).select_related('category')

    # 2. Apply search filter if a keyword is provided
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            # This line narrows down the 'products' queryset
            products = products.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))

    # 3. Apply category filter if a category_slug is provided
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        # This line further narrows down the 'products' queryset
        products = products.filter(category=category)

    # 4. Apply variation and price filters from GET parameters
    query_params = request.GET.copy()
    available_filters = {}
    # Build filters based on the already narrowed-down products
    variation_values = Variation.objects.filter(product__in=products).values_list('category__name', 'value').distinct()
    
    for category_name, value in variation_values:
        cat_name_lower = category_name.lower()
        if cat_name_lower not in available_filters:
            available_filters[cat_name_lower] = []
        if value not in available_filters[cat_name_lower]:
            available_filters[cat_name_lower].append(value)

    for category_name, values in query_params.lists():
        if category_name in available_filters and values:
            products = products.filter(
                variations__category__name__iexact=category_name, 
                variations__value__in=values
            )

    if min_price := query_params.get('min_price'):
        if min_price.isdigit():
            products = products.filter(product_price__gte=min_price)
    if max_price := query_params.get('max_price'):
        if max_price.isdigit():
            products = products.filter(product_price__lte=max_price)
    
    products = products.distinct().order_by('id')

    # 5. ✅ Calculate the count AFTER all filtering is complete
    product_count = products.count()

    # 6. Paginate the final, filtered queryset
    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    paged_products = paginator.get_page(page_number)

    # 7. Prepare the rest of the context
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True))
    else:
        try:
            wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
            wishlist_ids = list(WishlistItem.objects.filter(wishlist=wishlist).values_list('product_id', flat=True))
        except Wishlist.DoesNotExist:
            pass

    processed_filters = {}
    for category_name, available_values in available_filters.items():
        selected_values = request.GET.getlist(category_name)
        options = [{'value': value, 'is_selected': value in selected_values} for value in available_values]
        processed_filters[category_name] = options

    if 'page' in query_params:
        del query_params['page']

    context = {
        'products': paged_products,
        'product_count': product_count, # This count is now correct
        'wishlist_products': wishlist_ids,
        'processed_filters': processed_filters,
        'query_params': query_params.urlencode(),
        'category': category,
    }
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.prefetch_related(
            'variations__category', 
            'gallery'
        ).get(category__slug=category_slug, slug=product_slug, is_available=True)

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
        # return render(request, 'store/product_not_found.html')
    
    product_gallery = single_product.gallery.all()

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'variations_by_category': variations_by_category,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)
