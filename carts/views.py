from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

from accounts.models import UserProfile
from carts.models import Cart, CartItem
from store.models import Product, Variation

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# Create your views here.

def _cart_id(request): #private function
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variations = []

    if request.method == 'POST':
        print("Request POST data:", request.POST)

        for key, value in request.POST.items():
            print(f"Key: {key}, Value: {value}")
            if key.startswith('variation_'):
                variation_category = key.replace('variation_', '')
                print(f"Processing variation - Category: {variation_category}, Value: {value}")
                try:
                    variation = Variation.objects.get(
                        product=product,
                        category__name__iexact=variation_category,
                        value__iexact=value
                    )
                    product_variations.append(variation)
                    print(f"Added variation: {variation}")
                except Variation.DoesNotExist:
                    print(f"Variation not found for {variation_category} with value {value}")
                    pass
                
    cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    # Group cart items by user or by cart for anonymous users
    cart_items_query = CartItem.objects.filter(product=product)
    if request.user.is_authenticated:
        cart_items_query = cart_items_query.filter(user=request.user)
    else:
        cart_items_query = cart_items_query.filter(cart=cart)
    
    existing_item = None

    for item in cart_items_query:
        # Compare sets of variation IDs to see if we have an exact match
        if set(v.id for v in item.variations.all()) == set(v.id for v in product_variations):
            existing_item = item
            break

    if existing_item:
        existing_item.quantity += 1
        existing_item.save()
    else:
        new_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
            user=request.user if request.user.is_authenticated else None
        )
        if product_variations:
            new_item.variations.add(*product_variations)

    return redirect('cart')

def increment_cart_item(request, cart_item_id):
    """ Increments a cart item's quantity. """
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    
    # Check ownership
    is_owner = (request.user.is_authenticated and cart_item.user == request.user) or \
               (not request.user.is_authenticated and cart_item.cart.cart_id == _cart_id(request))

    if is_owner:
        # Check against stock
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.error(request, f"Only {cart_item.product.stock} units of {cart_item.product.product_name} available.")

    return redirect('cart')


def remove_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)

    # Basic authorization check
    is_owner = (request.user.is_authenticated and cart_item.user == request.user) or \
               (not request.user.is_authenticated and cart_item.cart.cart_id == _cart_id(request))

    if is_owner:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

def remove_cart_item(request, cart_item_id):
    """ Deletes a cart item entirely. """
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    
    is_owner = (request.user.is_authenticated and cart_item.user == request.user) or \
               (not request.user.is_authenticated and cart_item.cart.cart_id == _cart_id(request))

    if is_owner:
        cart_item.delete()
    return redirect('cart')

def cart(request):
    total = 0
    quantity = 0
    cart_items = []
    
    # ✅ PERFORMANCE FIX: Use select_related to fetch product and variation data in one query
    query = CartItem.objects.select_related('product').prefetch_related('variations__category')

    try:
        if request.user.is_authenticated:
            cart_items = query.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = query.filter(cart=cart, is_active=True)
        
        for item in cart_items:
            total += item.sub_total()
            quantity += item.quantity
    except ObjectDoesNotExist:
        pass # Ignore if cart/items don't exist

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request):
    # This view reuses the logic from the `cart` view but renders a different template.
    # We can keep it simple by just fetching the items again.
    total = 0
    quantity = 0
    cart_items = []
    
    try:
        cart_items = CartItem.objects.select_related('product').filter(user=request.user, is_active=True)
        for item in cart_items:
            total += item.sub_total()
            quantity += item.quantity
    except ObjectDoesNotExist:
        pass

    user_profile = UserProfile.objects.filter(user=request.user).first()

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'user_profile': user_profile,
    }
    return render(request, 'store/checkout.html', context)