import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Order, OrderItem, Category, OTP
from .otp_utils import generate_otp, send_otp_email

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

# Step 1 - Enter email to get OTP
def login_request_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email:
            return render(request, 'store/login_request_otp.html', {'error': 'Please enter your email!'})

        # Generate and save OTP
        otp_code = generate_otp()
        OTP.objects.create(phone_or_email=email, otp_code=otp_code)

        # Send OTP email
        try:
            send_otp_email(email, otp_code)
        except Exception as e:
            return render(request, 'store/login_request_otp.html', {'error': f'Failed to send OTP: {str(e)}'})

        # Save email in session
        request.session['otp_email'] = email
        return redirect('login_verify_otp')

    return render(request, 'store/login_request_otp.html')

# Step 2 - Enter OTP to login
def login_verify_otp(request):
    email = request.session.get('otp_email')
    if not email:
        return redirect('login_request_otp')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()

        # Find latest unused OTP for this email
        try:
            otp_obj = OTP.objects.filter(
                phone_or_email=email,
                is_used=False
            ).latest('created_at')
        except OTP.DoesNotExist:
            return render(request, 'store/login_verify_otp.html', {
                'error': 'OTP not found. Please request again.',
                'email': email
            })

        if not otp_obj.is_valid():
            return render(request, 'store/login_verify_otp.html', {
                'error': 'OTP expired! Please request a new one.',
                'email': email
            })

        if otp_obj.otp_code != entered_otp:
            return render(request, 'store/login_verify_otp.html', {
                'error': 'Wrong OTP! Please try again.',
                'email': email
            })

        # OTP is correct - mark as used
        otp_obj.is_used = True
        otp_obj.save()

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email}
        )

        # Login the user
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        del request.session['otp_email']
        return redirect('product_list')

    return render(request, 'store/login_verify_otp.html', {'email': email})

# Logout
def logout_view(request):
    logout(request)
    return redirect('login_request_otp')

# Test Cloudinary
def test_cloudinary(request):
    config = {
        'cloud_name': os.environ.get('CLOUD_NAME'),
        'api_key': os.environ.get('CLOUDINARY_API_KEY'),
        'api_secret': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    return JsonResponse(config)