import datetime
import json
from django.contrib import messages
from django.shortcuts import redirect, render

from carts.models import CartItem
from store.models import Product
from .forms import OrderForm
from .models import Order, OrderProduct, Payment

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

# Create your views here.
def payments(request):
    try:
        body = json.loads(request.body)
        print("Received body:", body)

        # Get the order that is not yet marked as ordered
        order = Order.objects.get(
            user=request.user,
            is_ordered=False,
            order_number=body['orderID']
        )

        # Save payment details
        payment = Payment(
            user=request.user,
            payment_id=body['transID'],
            payment_method=body['payment_method'],
            amount_paid=order.order_total,
            status=body['status'],
        )
        payment.save()

        # Mark order as paid
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Move cart items to OrderProduct table
        cart_items = CartItem.objects.filter(user=request.user)

        for cart in cart_items:
            order_product = OrderProduct()
            order_product.order_id = order.id
            order_product.payment = payment
            order_product.user_id = request.user.id
            order_product.product_id = cart.product_id
            order_product.quantity = cart.quantity
            order_product.product_price = cart.product.product_price
            order_product.product_unit_price = cart.product.product_price
            order_product.product_line_price = cart.product.product_price * cart.quantity
            order_product.ordered = True
            order_product.save()

            # Save variations
            product_variations = cart.variations.all()
            order_product.variations.set(product_variations)
            order_product.save()

            # Reduce stock
            product = Product.objects.get(id=cart.product_id)
            product.stock -= cart.quantity
            product.save()            

        # Clear the cart after moving items to orders
        CartItem.objects.filter(user=request.user).delete()

        messages.success(request, "Payment successfull")

        # Send Order Received Email
        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/order_received_email.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()

        messages.success(request, "Confirmation email sent")

        data = {
            'order_number' : order.order_number,
            'trans_ID' : payment.payment_id,
            'status' : 'success'
        }

        print(data)

        from django.http import JsonResponse

        return JsonResponse(data)

    except Exception as e:
        import traceback
        print("Payment save failed:", str(e))
        traceback.print_exc()

    # return render(request, 'orders/cart.html')

def place_order(request):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0
    total = 0
    quantity = 0
    
    for cart_item in cart_items:
            total += (cart_item.product.product_price * cart_item.quantity)
            quantity += cart_item.quantity

    tax = (2 * total) / 100  # Assuming a tax rate of 2%
    grand_total = total + tax
    
    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items' : cart_items,
                'total' : total,
                'tax' : tax,
                'grand_total' : grand_total
            }

            messages.success(request, "Order placed successfully")
            return render(request, 'orders/payments.html', context)
        
        else:
            return redirect('checkout')

def order_complete(request):
    print('get into order complete view')
    order_number = request.GET.get('order_number')
    trans_ID = request.GET.get('payment_id')
    print(order_number, trans_ID)

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=trans_ID)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_line_price

        context = {
            'order' : order,
            'payment' : payment,
            'ordered_products' : ordered_products,
            'order_number' : order.order_number,
            'trans_ID' : payment.payment_id,
            'subtotal' : subtotal,
        }
    
        return render(request, 'orders/order_complete.html', context)
    
    except (Payment.DoesNotExist, Order.DoesNotExist):
        print('here problem occuring')
        return redirect('orders/order_complete.html')