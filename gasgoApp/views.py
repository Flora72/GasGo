import json
from django.http import HttpResponse , JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order
import uuid
from . import models



# -------------------------------------
#  GENERAL VIEWS
# --------------------------------------
def index(request):
    return render(request, 'index.html')
def about(request):
    return render(request, 'about.html')
def contact(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        topic = request.POST.get('topic')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        order_id = request.POST.get('order_id')
        urgent = request.POST.get('urgent')
        reply_via = request.POST.get('reply_via')
        best_time = request.POST.get('best_time')
        consent = request.POST.get('consent')

        # Save users messages and send notification (Placeholder)
        messages.success(request, "Your message has been sent. We'll get back to you shortly.")
        return redirect('contact')

    return render(request, 'contact.html')
def testimonials(request):
    return render(request, 'testimonials.html')
def emergency(request):
    return render(request, 'emergency.html')
def gasbot(request):
    return render(request, 'gasbot.html')

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard.html')

# -------------------------------------
#  AUTH RELATED VIEWS
# --------------------------------------
def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'signup.html')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Optional: Save phone/address to user profile if you have a custom model
        # e.g., Profile.objects.create(user=user, phone=phone, address=address)

        messages.success(request, "Account created successfully.")
        return redirect('login')

    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        # AuthenticationForm expects 'username' and 'password'
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")

    # For GET requests or failed POST requests
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        try:
            # 1. Get the email from the frontend request body
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({"message": "Email is required"}, status=400)

            # 2. Use Django's PasswordResetForm to handle the logic
            form = PasswordResetForm({'email': email})

            if form.is_valid():
                form.save(
                    request=request,
                    email_template_name='emails/password_reset_email.html',
                    from_email='GasGo Assistance <gasgoassistance@gmail.com>',
                    subject_template_name='emails/password_reset_subject.txt',
                )

            # 3. Security Best Practice: Always return a generic success message
            return JsonResponse({
                "message": "If the email is registered, a password reset link has been sent."
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid data format"}, status=400)
        except ValidationError:
            # Catch errors like invalid email format, but still return success message
            pass

    # If the method is GET (user is just browsing to the page), render the HTML form
    return render(request, 'forgot_password.html')

# -------------------------------------
#    ORDER & VENDOR VIEWS
# --------------------------------------

@login_required(login_url='login')
def order(request):
    if request.method == 'POST':
        # --- 1. Extract Order Data ---
        order_details = {
            'size': request.POST.get('size'),
            'brand': request.POST.get('brand'),
            'exchange': request.POST.get('exchange'),
            'quantity': request.POST.get('quantity'),
            'full_name': request.POST.get('full_name'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'directions': request.POST.get('directions'),
            'preferred_time': request.POST.get('preferred_time'),
            'notes': request.POST.get('notes'),
        }

        # --- 2. Basic Validation ---
        if not order_details['size'] or not order_details['address'] or not order_details['phone']:
            messages.error(request, "Please fill in all required fields (Size, Address, Phone).")
            return render(request, 'order.html', {'order_details': order_details})

        # --- 3. Save/Store Initial Order (Simulation) ---
        request.session['pending_order_data'] = order_details
        messages.info(request, "Step 1 complete. Now choose your vendor and payment method.")
        return redirect('vendors')

    return render(request, 'order.html')

@login_required(login_url='login')
def track_order(request):
    user = request.user
    order_id = request.GET.get('order_id')

    order = None
    tracking_mode = 'demo'

    if order_id:
        try:
            order = Order.objects.get(order_id=order_id, user=user)
            tracking_mode = 'live'
        except Order.DoesNotExist:
            messages.warning(request, "We couldn't find an order with that ID.")
    else:
        order = Order.objects.filter(user=user).order_by('-created_at').first()
        if order:
            tracking_mode = 'latest'

    if not order:
        messages.info(request, "No active orders found. Showing demo tracking.")
        return render(request, 'track_order.html', {
            'demo_mode': True,
            'tracking_mode': tracking_mode,
            'rider_lat': None,
            'rider_lng': None,
            'user_lat': None,
            'user_lng': None,
            'order': None,
        })

    # Safely extract coordinates
    rider_lat = getattr(order, 'rider_latitude', None)
    rider_lng = getattr(order, 'rider_longitude', None)
    user_lat = getattr(order, 'delivery_latitude', None)
    user_lng = getattr(order, 'delivery_longitude', None)

    context = {
        'order': order,
        'demo_mode': False,
        'tracking_mode': tracking_mode,
        'rider_lat': rider_lat,
        'rider_lng': rider_lng,
        'user_lat': user_lat,
        'user_lng': user_lng,
    }
    return render(request, 'track_order.html', context)

# @login_required
def vendors(request):
    if request.method == 'POST':
        # Get data from the submitted form (Vendor/Payment)
        vendor_choice = request.POST.get('vendor_choice')
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes')
        
        # Retrieve initial order data from session (simulation)
        pending_order_data = request.session.get('pending_order_data', {})
        
        # 1. Validation 
        if not vendor_choice or not payment_method:
            messages.error(request, "Please select a vendor and a payment method.")
            return render(request, 'vendors.html')
            
        # 2. Finalize Order (Simulation)
        # In a real app, you would:
        # a. Fetch the pending Order object 
        # b. Update it: order.vendor = vendor_choice, order.payment_method = payment_method, etc.
        # c. Set status: order.status = 'Confirmed'
        # d. order.save()
        
        # Clear session data once order is confirmed
        if 'pending_order_data' in request.session:
            del request.session['pending_order_data']

        # 3. Success message and redirect
        messages.success(request, f"Order confirmed! Vendor: {vendor_choice}, Payment: {payment_method}. We're assigning a rider now.")
        
        # Redirect the user to the tracking page
        return redirect('track_order')

    # For GET requests, render the vendor selection page
    return render(request, 'vendors.html')