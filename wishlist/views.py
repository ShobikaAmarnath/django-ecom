from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from wishlist.models import Wishlist, WishlistItem
from django.contrib import messages

def _wishlist_id(request):
    wishlist = request.session.session_key
    if not wishlist:
        request.session.create()   # ensure a new session is created
        wishlist = request.session.session_key
    return wishlist

# ✅ Show wishlist page
def wishlist(request):
    if request.user.is_authenticated:
        items = WishlistItem.objects.filter(user=request.user, is_active=True)
    else:
        wishlist_obj, _ = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))
        items = WishlistItem.objects.filter(wishlist=wishlist_obj, is_active=True)

    context = {
        'wishlist_items': items,
        'wishlist_count': items.count(),
    }
    return render(request, 'store/wishlist.html', context)

# ❌ Remove item from wishlist
from django.views.decorators.http import require_POST

@require_POST
def remove_from_wishlist(request, item_id):
    try:
        item = WishlistItem.objects.get(id=item_id)
    except WishlistItem.DoesNotExist:
        return redirect(request.META.get('HTTP_REFERER', 'store'))

    if request.user.is_authenticated and item.user == request.user:
        item.delete()
    elif not request.user.is_authenticated and item.wishlist.wishlist_id == _wishlist_id(request):
        item.delete()

    return redirect(request.META.get('HTTP_REFERER', 'store'))

# 🔁 Toggle wishlist (add if not in, remove if already in)
def toggle_wishlist(request, product_id):
    print("Toggling wishlist for product ID:", product_id)
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        item, created = WishlistItem.objects.get_or_create(product=product, user=request.user, is_active=True)
    else:
        wishlist_obj, _ = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))
        item, created = WishlistItem.objects.get_or_create(product=product, wishlist=wishlist_obj, is_active=True)

    if not created:
        item.delete()

    return redirect(request.META.get('HTTP_REFERER', 'store'))

