import datetime
import json
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.contrib.auth.decorators import login_required

from carts.models import CartItem
from .forms import OrderForm
from .models import Order, OrderProduct, Payment

SHOP_OWNER_EMAIL = settings.SHOP_OWNER_EMAIL

def send_order_emails(order, payment):
    """ Sends customized HTML emails to the customer and owner based on the payment method. """
    # --- Send Confirmation to Customer ---
    customer_subject = 'Thank You For Your Order!'
    customer_template = 'orders/order_received_email.html'
    subtotal = order.order_total - order.shipping_charge
    customer_context = {'user': order.user, 'order': order, 'payment': payment, 'subtotal': subtotal}
    customer_message = render_to_string(customer_template, customer_context)
    customer_email = EmailMessage(customer_subject, customer_message, to=[order.email])
    customer_email.content_subtype = "html"
    customer_email.send()

    # --- Send Notification to Shop Owner ---
    if payment.payment_method == 'UPI' and payment.status == 'Pending':
        owner_subject = f"ACTION REQUIRED: Verify UPI Payment for Order #{order.order_number}"
        owner_template = 'orders/owner_verify_payment_email.html'
    else:
        owner_subject = f"New Order Received - #{order.order_number}"
        owner_template = 'orders/owner_new_order_email.html'
    
    owner_context = {'order': order, 'payment': payment}
    owner_message = render_to_string(owner_template, owner_context)
    owner_email = EmailMessage(owner_subject, owner_message, to=[SHOP_OWNER_EMAIL])
    owner_email.content_subtype = "html"
    owner_email.send()

@transaction.atomic
def payments(request):
    try:
        body = json.loads(request.body)
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
        payment = Payment.objects.create(
            user=request.user,
            payment_id=body['transID'],
            payment_method=body['payment_method'],
            amount_paid=order.order_total,
            status=body['status']
        )
        order.payment = payment
        order.is_ordered = True
        order.save()

        cart_items = CartItem.objects.filter(user=request.user).select_related('product').prefetch_related('variations')
        for item in cart_items:
            order_product = OrderProduct(
                order=order, payment=payment, user=request.user, product=item.product,
                quantity=item.quantity, product_unit_price=item.product.product_price,
                product_line_price=item.sub_total(), ordered=True
            )
            order_product.save()
            order_product.variations.set(item.variations.all())
            item.product.stock -= item.quantity
            item.product.save()

        CartItem.objects.filter(user=request.user).delete()
        send_order_emails(order, payment)
        data = {'order_number': order.order_number, 'trans_ID': payment.payment_id, 'status': 'success'}
        return JsonResponse(data)
    
    # ✅ This block will handle the specific error if the order is not found
    except Order.DoesNotExist:
        error_message = "Order not found. It might have already been processed or does not exist."
        return JsonResponse({'status': 'failed', 'error': error_message}, status=404)
    
    # This block will catch any other unexpected errors
    except Exception as e:
        import traceback
        traceback.print_exc() # This will print the full error to your terminal for debugging
        return JsonResponse({'status': 'failed', 'error': str(e)}, status=400)

def place_order(request):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user).select_related('product')
    
    if not cart_items.exists():
        return redirect('store')

    total = sum(item.sub_total() for item in cart_items)
    total_weight = sum(item.product.weight * item.quantity for item in cart_items)
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            state_from_form = form.cleaned_data['state']
            shipping_rate = Decimal('60.00') if state_from_form.strip().lower() == 'tamil nadu' else Decimal('100.00')
            shipping_charge = (total_weight * shipping_rate).quantize(Decimal('0.01'))
            grand_total = total + shipping_charge
            
            data = form.save(commit=False)
            data.user = current_user
            data.order_total = grand_total
            data.shipping_charge = shipping_charge
            data.ip = request.META.get('REMOTE_ADDR')
            data.is_ordered = False
            data.save()

            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = f"{current_date}{data.id}"
            data.order_number = order_number
            data.save()

            context = {
                'order': data, 'cart_items': cart_items, 'total': total,
                'delivery_charge': shipping_charge, 'grand_total': grand_total,
                'UPI_ID': settings.UPI_ID, 'UPI_NAME': settings.UPI_NAME,
            }
            return render(request, 'orders/payments.html', context)
    return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    trans_ID = request.GET.get('payment_id')

    try:
        # ✅ FINAL SECURITY FIX: Ensure the user owns the order
        order = Order.objects.get(order_number=order_number, is_ordered=True, user=request.user)
        ordered_products = OrderProduct.objects.filter(order=order).select_related('product').prefetch_related('variations__category')
        payment = Payment.objects.get(payment_id=trans_ID)
        subtotal = sum(item.product_line_price for item in ordered_products)
        context = {
            'order': order, 'payment': payment,
            'ordered_products': ordered_products, 'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    
@login_required(login_url='login')
def order_detail(request, order_number):
    try:
        # Fetch the order and all related items in an efficient way
        order = Order.objects.get(order_number=order_number, user=request.user)
        ordered_products = OrderProduct.objects.filter(order=order).select_related('product').prefetch_related('variations__category')
        
        # Calculate the subtotal
        subtotal = order.order_total - order.shipping_charge

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'subtotal': subtotal,
        }
        return render(request, 'accounts/order_detail.html', context)
    except Order.DoesNotExist:
        return redirect('dashboard')