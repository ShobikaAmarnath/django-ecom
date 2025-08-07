from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from wishlist.models import Wishlist, WishlistItem


def _wishlist_id(request):
    wishlist = request.session.session_key
    if not wishlist:
        wishlist = request.session.create()
    return wishlist


# ✅ Show wishlist page
def wishlist(request):
    wishlist_id = _wishlist_id(request)
    wishlist_obj, created = Wishlist.objects.get_or_create(wishlist_id=wishlist_id)

    items = WishlistItem.objects.filter(wishlist=wishlist_obj, is_active=True)

    context = {
        'wishlist_items': items,
        'wishlist_count': items.count(),
    }
    return render(request, 'store/wishlist.html', context)


# ➕ Add item to wishlist
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_obj, _ = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))

    WishlistItem.objects.get_or_create(product=product, wishlist=wishlist_obj, is_active=True)
    return redirect(request.META.get('HTTP_REFERER', 'store'))


# ❌ Remove item from wishlist
def remove_from_wishlist(request, product_id):
    wishlist_id = _wishlist_id(request)
    wishlist_obj = get_object_or_404(Wishlist, wishlist_id=wishlist_id)

    WishlistItem.objects.filter(product_id=product_id, wishlist=wishlist_obj).delete()
    return redirect(request.META.get('HTTP_REFERER', 'store'))


# 🔁 Toggle wishlist (add if not in, remove if already in)
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_obj, _ = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))

    item, created = WishlistItem.objects.get_or_create(product=product, wishlist=wishlist_obj, is_active=True)

    if not created:
        item.delete()

    return redirect(request.META.get('HTTP_REFERER', 'store'))

def product_list(request):
    products = Product.objects.all()
    
    wishlist_ids = []
    try:
        wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
        wishlist_ids = list(WishlistItem.objects.filter(wishlist=wishlist).values_list('product_id', flat=True))
    except Wishlist.DoesNotExist:
        pass

    context = {
        'products': products,
        'wishlist_products': wishlist_ids,
    }
    return render(request, 'store/product_list.html', context)