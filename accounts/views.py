from django.shortcuts import render, redirect
from accounts.models import Account, UserProfile
from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order
from wishlist.models import Wishlist, WishlistItem
from wishlist.views import _wishlist_id
from .forms import RegistrationForm, EditProfileForm, UserProfileForm
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
import requests

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            phone_number = form.cleaned_data['phone_number']
            username = email

            if Account.objects.filter(email=email).exists():
                messages.error(request, 'An account with this email address already exists.')
                return redirect('register')

            user = Account.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                username=username,
                password=password,
            )
            user.phone_number = phone_number
            user.save()

            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.content_subtype = "html"  # Main content is now text/html
            send_email.send()

            messages.success(request, "Thank you for registering. A confirmation email has been sent to your email address.")
            return redirect('/accounts/login/?command=verification&email=' + email)
    
    else:
        form = RegistrationForm()
        
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

from django.contrib.auth import authenticate, login as auth_login

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect('login')

        user = authenticate(email=email, password=password)

        if user is not None:
            # Merge Guest Cart → User Cart
            try:
                session_cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
                if session_cart:
                    session_cart_items = CartItem.objects.filter(cart=session_cart, user=None)
                    for item in session_cart_items:
                        matching_items = CartItem.objects.filter(user=user, product=item.product)

                        same_variation_item = None
                        item_variations_ids = sorted([v.id for v in item.variations.all()])

                        for user_item in matching_items:
                            user_item_variations_ids = sorted([v.id for v in user_item.variations.all()])
                            if item_variations_ids == user_item_variations_ids:
                                same_variation_item = user_item
                                break

                        if same_variation_item:
                            same_variation_item.quantity += item.quantity
                            same_variation_item.save()
                            item.delete()
                        else:
                            item.user = user
                            item.cart = None
                            item.save()
            except Cart.DoesNotExist:
                pass

            # Merge Guest Wishlist → User Wishlist
            try:
                guest_wishlist = Wishlist.objects.filter(wishlist_id=_wishlist_id(request)).first()
                if guest_wishlist:
                    guest_items = WishlistItem.objects.filter(wishlist=guest_wishlist, user=None)
                    for item in guest_items:
                        # Avoid duplicate products in wishlist
                        if not WishlistItem.objects.filter(user=user, product=item.product).exists():
                            item.user = user
                            item.wishlist = None
                            item.save()
                        else:
                            item.delete()
            except Wishlist.DoesNotExist:
                pass

            # Log the user in
            auth_login(request, user)
            messages.success(request, "Login successful.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated successfully.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid or has expired.")
        return redirect('register')
    
@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def forgotPassword(request):
    if request.method == "POST":
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            current_site = get_current_site(request)
            mail_subject = "Reset your Password"
            message = render_to_string('accounts/reset_password.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Link sent')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist')
            return redirect('register')
        
    return render(request, 'accounts/forgotPassword.html')

def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, "Your Password Reset link is validated successfull")
        return redirect('resetPassword')
    else:
        messages.error(request, "Activation link is invalid or has expired.")
        return redirect('login')
    
def resetPassword(request):

    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()

            messages.success(request, "Reset password successfull!")
            return redirect('login')
        else:
            messages.error(request, "Passwords don't match!")
            return redirect('resetPassword')
        
    else:
        return render(request, 'accounts/resetPassword.html')

def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/dashboard.html', context)

def order_detail(request, order_id):
    print("ORDER ID : ", order_id)
    order = Order.objects.get(order_number=order_id, user=request.user)
    ordered_products = order.orderproduct_set.all()

    context = {
        'order': order,
        'ordered_products': ordered_products,
    }
    print("ORDER DETAILS : ", ordered_products)
    return render(request, 'accounts/order_detail.html', context)

@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('dashboard')
    else:
        form = EditProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

    context = {
        'form': form,
        'profile_form': profile_form,
        'user_profile': user_profile,
    }
    return render(request, 'accounts/edit_profile.html', context)

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Important: keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated successfully.")
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(user=request.user)

    context = {'form': form}
    return render(request, 'accounts/change_password.html', context)