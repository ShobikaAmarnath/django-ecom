from django.http import HttpResponse
from django.shortcuts import render
from store.models import Product
from wishlist.models import Wishlist, WishlistItem
from wishlist.views import _wishlist_id

def home(request):
    latest_products = Product.objects.order_by('-created_date')[:6]
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_items = WishlistItem.objects.filter(user=request.user, is_active=True)
    else:
        wishlist_obj, _ = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist_obj, is_active=True)

    wishlist_ids = list(wishlist_items.values_list('product_id', flat=True))
    context = {
        'products': latest_products,
        'wishlist_products': wishlist_ids,
    }
    return render(request, 'home.html', context)