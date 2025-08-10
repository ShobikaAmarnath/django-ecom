from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from carts.models import Cart, CartItem
from store.models import Product, Variation

from django.contrib.auth.decorators import login_required

# Create your views here.

def _cart_id(request): #private function
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    if request.method == 'POST':
        print("Request POST data:", request.POST)

        for key, value in request.POST.items():
            if key.startswith('radio_') and value:
                variation_category = key.replace('radio_', '')
                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=variation_category,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                    print(f"Added variation: {variation}")
                except Variation.DoesNotExist:
                    print(f"Variation not found for {variation_category} with value {value}")


    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    # Check if cart item with same variations exists
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
    existing_item = None
    current_variation_ids = sorted([v.id for v in product_variation])

    for item in cart_items:
        existing_variation_ids = sorted([v.id for v in item.variations.all()])
        if existing_variation_ids == current_variation_ids:
            existing_item = item
            break

    if existing_item:
        if existing_item.quantity < existing_item.product.stock:
            existing_item.quantity += 1
            existing_item.save()
    else:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            user=request.user if request.user.is_authenticated else None,
            cart=None if request.user.is_authenticated else cart
        )
        if len(product_variation) > 0:
            cart_item.variations.set(product_variation)
        cart_item.save()

    return redirect('cart')


def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        try:
            cart_item = CartItem.objects.get(product=product, user=request.user)
        except CartItem.DoesNotExist:
            cart_item = None
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        try:
            cart_item = CartItem.objects.get(product=product, cart=cart)
        except CartItem.DoesNotExist:
            cart_item = None

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('cart')


from django.views.decorators.http import require_POST

@require_POST
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
    except CartItem.DoesNotExist:
        return redirect('cart')

    if request.user.is_authenticated:
        if cart_item.user == request.user:
            cart_item.delete()
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            if cart_item.cart == cart:
                cart_item.delete()
        except Cart.DoesNotExist:
            pass

    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.product_price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100  # Assuming a tax rate of 2%
        grand_total = total + tax

    except Cart.DoesNotExist:
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'cart_count': cart_items.count() if cart_items else 0,
    }

    return render(request, 'store/cart.html', context)

@login_required(login_url= 'login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.product_price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100  # Assuming a tax rate of 2%
        grand_total = total + tax

    except Cart.DoesNotExist:
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'cart_count': cart_items.count() if cart_items else 0,
    }
    return render(request, 'store/checkout.html', context)