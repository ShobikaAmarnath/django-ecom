from .models import Wishlist, WishlistItem
from .views import _wishlist_id

def wishlist_counter(request):
    wishlist_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            wishlist = Wishlist.objects.filter(wishlist_id=_wishlist_id(request)).first()
            if wishlist:
                wishlist_items = WishlistItem.objects.filter(wishlist=wishlist, is_active=True)
                wishlist_count = wishlist_items.count()
            else:
                wishlist_count = 0
        except Wishlist.DoesNotExist:
            wishlist_count = 0
    return dict(wishlist_count=wishlist_count)

def wishlist_products_ids(request):
    wishlist_ids = []
    try:
        wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
        wishlist_ids = list(WishlistItem.objects.filter(wishlist=wishlist).values_list('product_id', flat=True))
    except Wishlist.DoesNotExist:
        pass
    return {'wishlist_products': wishlist_ids}