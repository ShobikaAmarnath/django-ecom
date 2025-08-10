from .models import Wishlist, WishlistItem
from .views import _wishlist_id

def wishlist_counter(request):
    wishlist_count = 0
    if 'admin' in request.path:
        return {}
    
    try:
        if request.user.is_authenticated:
            wishlist_items = WishlistItem.objects.filter(user=request.user, is_active=True)
        else:
            wishlist = Wishlist.objects.filter(wishlist_id=_wishlist_id(request)).first()
            wishlist_items = WishlistItem.objects.filter(wishlist=wishlist, is_active=True) if wishlist else []
        
        wishlist_count = wishlist_items.count()
    except:
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