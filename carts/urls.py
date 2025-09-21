from django.urls import path

from . import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'), #Adds item to cart
    path('increment_cart_item/<int:cart_item_id>/', views.increment_cart_item, name='increment_cart_item'), #Increments quantity
    path('remove_cart/<int:cart_item_id>/', views.remove_cart, name='remove_cart'), #Decrements quantity 
    path('remove_cart_item/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'), #Removes item completely
    path('checkout/', views.checkout, name='checkout'),
]