import datetime
import json
import decimal
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

SHOP_OWNER_EMAIL = 'amarnathshobika@gmail.com'

def send_emails(order, payment):
    """
    Send emails according to payment method.
    Notifies customer and shop owner as needed.
    """

    # ===== PAYPAL - auto confirmed =====
    if payment.payment_method == "PayPal":
        # Customer email
        subject_cust = "Order Confirmed - Thank you!"
        message_cust = render_to_string('orders/order_received_email.html', {
            'user': order.user,
            'order': order,
            'payment_confirmed': True,
            'message': "Your payment via PayPal has been successfully received. Your order is confirmed."
        })
        EmailMessage(subject_cust, message_cust, to=[order.user.email]).send()

        # Owner notification
        subject_owner = f"New PayPal Order Received - {order.order_number}"
        message_owner = f"""
        Hi,

        A new order has been placed and auto-confirmed via PayPal.

        Order Number: {order.order_number}
        Customer: {order.full_name()}
        Amount: {order.order_total}

        No manual action is required.
        """
        EmailMessage(subject_owner, message_owner, to=[SHOP_OWNER_EMAIL]).send()

    # ===== UPI - manual verification needed =====
    elif payment.payment_method == "UPI":
        # Customer email
        subject_cust = f"Order Received - Payment Pending Verification"
        message_cust = f"""
        Hi {order.user.first_name},

        Thank you for placing your order #{order.order_number}.
        Your payment via UPI is pending verification.

        The shop owner will confirm your payment shortly.
        """
        EmailMessage(subject_cust, message_cust, to=[order.user.email]).send()

        # Owner email
        subject_owner = f"New UPI Payment Pending - {order.order_number}"
        message_owner = f"""
        Hi,

        A customer has placed an order using UPI.
        Order Number: {order.order_number}
        Customer: {order.full_name()}
        Amount: {order.order_total}

        Please verify the payment and update the order status in the admin panel.
        """
        EmailMessage(subject_owner, message_owner, to=[SHOP_OWNER_EMAIL]).send()

    # ===== COD - cash on delivery =====
    elif payment.payment_method == "COD":
        # Customer email
        subject_cust = f"Order Placed - Cash on Delivery"
        message_cust = f"""
        Hi {order.user.first_name},

        Your order #{order.order_number} has been successfully placed.
        Payment will be collected upon delivery.

        Thank you for shopping with us!
        """
        EmailMessage(subject_cust, message_cust, to=[order.user.email]).send()

        # Owner notification
        subject_owner = f"New COD Order - {order.order_number}"
        message_owner = f"""
        Hi,

        A new order has been placed with Cash on Delivery.
        Order Number: {order.order_number}
        Customer: {order.full_name()}
        Amount: {order.order_total}

        Please prepare the order for delivery.
        """
        EmailMessage(subject_owner, message_owner, to=[SHOP_OWNER_EMAIL]).send()

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
        if body['payment_method'] == "PayPal":
            order.status = 'Paid'
        elif body['payment_method'] == "UPI":
            order.status = 'Pending'
        elif body['payment_method'] == "COD":
            order.status = 'Pending'
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

        send_emails(order, payment)

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
        from django.http import JsonResponse
        return JsonResponse({'status': 'failed', 'error': str(e)})

    # return render(request, 'orders/cart.html')

def place_order(request):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    total = 0
    quantity = 0
    shipping_charge = 0
    total_weight = 0
    
    for cart_item in cart_items:
            total += (cart_item.product.product_price * cart_item.quantity)
            quantity += cart_item.quantity
            total_weight += (cart_item.product.weight * cart_item.quantity)

    grand_total = total
    
    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
            state_from_form = form.cleaned_data['state']
            total_weight_decimal = decimal.Decimal(total_weight)
            if state_from_form.strip().lower() == 'tamil nadu':
                shipping_charge_per_kg = decimal.Decimal('60.00')
            else:
                shipping_charge_per_kg = decimal.Decimal('100.00')

            shipping_charge = total_weight_decimal * shipping_charge_per_kg
            shipping_charge = round(shipping_charge, 2)

            grand_total += shipping_charge
            
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
            data.shipping_charge = shipping_charge
            data.ip = request.META.get('REMOTE_ADDR')
            data.status = 'Pending'
            data.is_ordered = False
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
                'delivery_charge': shipping_charge,
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
        order = Order.objects.get(order_number=order_number)
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
        return redirect('store')