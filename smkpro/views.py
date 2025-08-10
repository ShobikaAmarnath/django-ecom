from django.http import HttpResponse
from django.shortcuts import render
from store.models import Product

def home(request):
    latest_products = Product.objects.order_by('-created_date')[:6]
    context = {
        'products': latest_products,
    }
    return render(request, 'home.html', context)