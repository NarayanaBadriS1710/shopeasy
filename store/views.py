import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Order, OrderItem, Category
from .forms import RegisterForm

# Show all products
def product_list(request):
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None
    })

# Show single product
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

# Add to cart
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order, created = Order.objects.get_or_create(user=request.user, is_paid=False)
    item, created = OrderItem.objects.get_or_create(order=order, product=product)
    if not created:
        item.quantity += 1
        item.save()
    return redirect('cart')

# View cart
@login_required
def cart(request):
    try:
        order = Order.objects.get(user=request.user, is_paid=False)
    except Order.DoesNotExist:
        order = None
    return render(request, 'store/cart.html', {'order': order})

# Place order
@login_required
def place_order(request):
    try:
        order = Order.objects.get(user=request.user, is_paid=False)
        order.is_paid = True
        order.save()
        return redirect('order_confirmation')
    except Order.DoesNotExist:
        return redirect('cart')

# Order confirmation
@login_required
def order_confirmation(request):
    try:
        order = Order.objects.filter(user=request.user, is_paid=True).latest('created_at')
    except Order.DoesNotExist:
        order = None
    return render(request, 'store/order_confirmation.html', {'order': order})

# Register
def register_view(request):
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('product_list')
    return render(request, 'store/register.html', {'form': form})

# Login
def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('product_list')
        else:
            error = "Invalid username or password!"
    return render(request, 'store/login.html', {'error': error})

# Logout
def logout_view(request):
    logout(request)
    return redirect('login')

# Test Cloudinary
def test_cloudinary(request):
    config = {
        'cloud_name': os.environ.get('CLOUD_NAME'),
        'api_key': os.environ.get('CLOUDINARY_API_KEY'),
        'api_secret': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    return JsonResponse(config)