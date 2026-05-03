from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.product_list,       name='product_list'),
    path('product/<int:pk>/',   views.product_detail,     name='product_detail'),
    path('add/<int:pk>/',       views.add_to_cart,        name='add_to_cart'),
    path('cart/',               views.cart,               name='cart'),
    path('place-order/',        views.place_order,        name='place_order'),
    path('order-confirmation/', views.order_confirmation, name='order_confirmation'),
    path('register/',           views.register_view,      name='register'),
    path('login/',              views.login_view,         name='login'),
    path('logout/',             views.logout_view,        name='logout'),
    path('test-cloudinary/',    views.test_cloudinary,    name='test_cloudinary'),
]