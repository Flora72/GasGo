import json, requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout 
from django.contrib.auth.decorators import login_required
from .models import Order , Profile , Vendor
from .mpesa_integration import initiate_stk_push
from decouple import config

# -------------------------------------
# GENERAL VIEWS
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

        messages.success(request, "Your message has been sent. We'll get back to you shortly.")
        return redirect('contact')

    return render(request, 'contact.html')
def testimonials(request):
    return render(request, 'testimonials.html')

@login_required(login_url='login')
def emergency(request):
    return render(request, 'emergency.html')
def gasbot(request):
    return render(request, 'gasbot.html')
def dashboard(request):
    return render(request, 'dashboard.html')

# -------------------------------------
# AUTH RELATED VIEWS
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

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with that email already exists.")
            return render(request, 'signup.html')

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        user.save()

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
#  ORDER & VENDOR VIEWS
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
            # Re-render the form with existing data if possible
            return render(request, 'order.html', {'order_details': order_details})

        # --- 3. Save/Store Initial Order (Simulation) ---
        # In a real application, you would create an Order object here:
        # new_order = Order.objects.create(user=request.user, **order_details, status='Draft')
        
        # Using session to pass data to the next step (vendors page)
        request.session['pending_order_data'] = order_details
        
        messages.info(request, "Step 1 complete. Now choose your vendor and payment method.")
        
        # --- 4. Redirect to next step: Vendors ---
        return redirect('available_vendors')
        
    return render(request, 'order.html')

@login_required(login_url='login')
def confirm_order(request):
    if request.method == 'POST':
        # --- 1. Retrieve Pending Order Data from Session ---
        pending_order_data = request.session.get('pending_order_data')
        if not pending_order_data:
            messages.error(request, "Session expired or missing order data. Please start again.")
            return redirect('order')

        # --- 2. Extract Vendor and Notes from Form ---
        vendor_name = request.POST.get('vendor_choice')
        notes = request.POST.get('notes', '')

        if not vendor_name:
            messages.error(request, "Please select a vendor to proceed.")
            return redirect('available_vendors')

        # --- 3. Combine All Data ---
        final_order_data = {
            **pending_order_data,
            'vendor': vendor_name,
            'notes': notes,
            'user': request.user,
            'status': 'Pending'
        }

        # --- 4. Save to Database ---
        try:
            new_order = Order.objects.create(**final_order_data)
            # Optionally clear session
            del request.session['pending_order_data']
            messages.success(request, "Order confirmed! Proceed to payment.")
            return redirect('payment', order_id=new_order.id)
        except Exception as e:
            print("Order creation failed:", e)
            messages.error(request, "Something went wrong while confirming your order.")
            return redirect('available_vendors')

    # If GET request, redirect to order page
    return redirect('order')

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

    context = {
        'order': order,
        'demo_mode': False,
        'tracking_mode': tracking_mode,
        'rider_lat': float(order.rider_latitude or 0),
        'rider_lng': float(order.rider_longitude or 0),
        'user_lat': float(order.delivery_latitude or 0),
        'user_lng': float(order.delivery_longitude or 0),
    }
    return render(request, 'track_order.html', context)

@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Check if a file was sent with the request
        if 'profile_image' in request.FILES:
            # Assign the uploaded file to the model field
            user_profile.profile_image = request.FILES['profile_image']
            user_profile.save()
            # Redirect to the profile page to prevent form resubmission
            return redirect('profile') 

    context = {
        'user_profile': user_profile,
        # ... other context data
    }
    return render(request, 'profile.html', context)

def history(request):
    return render(request, 'history.html')

@login_required 
def vendors(request):
    if request.method == 'POST':
        vendor_choice = request.POST.get('vendor_choice')
        payment_method = request.POST.get('payment_method')
        final_notes = request.POST.get('notes')
        
        pending_order_data = request.session.get('pending_order_data', {})
        
        # 1. VALIDATION
        if not vendor_choice or not payment_method or not pending_order_data:
            messages.error(request, "Order data is incomplete. Please start the order again.")
            return redirect('orders')
        
        # 2. CREATE OR GET VENDOR
        selected_vendor, _ = Vendor.objects.get_or_create(name=vendor_choice)

        # 3. CREATE ORDER
        total_cost = 3200.00  # Replace with dynamic pricing if needed
        new_order = Order.objects.create(
            user=request.user,
            vendor=selected_vendor,
            status='Pending Payment', 
            total_cost=total_cost,
            notes=final_notes,
            size=pending_order_data.get('size'),
            brand=pending_order_data.get('brand'),
            exchange=pending_order_data.get('exchange'),
            quantity=pending_order_data.get('quantity', 1),
            full_name=pending_order_data.get('full_name'),
            phone=pending_order_data.get('phone'),
            address=pending_order_data.get('address'),
            directions=pending_order_data.get('directions'),
            preferred_time=pending_order_data.get('preferred_time'),
        )
        
        # 4. CLEAR SESSION
        request.session.pop('pending_order_data', None)
        
        # 5. REDIRECT
        if payment_method == 'M-Pesa':
            messages.info(request, "Redirecting to M-Pesa payment portal...")
            return redirect('initiate_payment', order_id=new_order.order_id)
        else:
            new_order.status = 'Confirmed'
            new_order.save()
            messages.success(request, f"Order {new_order.order_id} confirmed! Rider assignment in progress.")
            return redirect('track_order')

    # GET request fallback
    vendors = Vendor.objects.all()
    return render(request, 'vendors.html', {'vendors': vendors})
# PAYMENT VIEWS (m-pesa integration)
# --------------------------------------
def format_phone_number(number):
    number = str(number)
    if number.startswith('0'):
        return '254' + number[1:]
    elif number.startswith('+254'):
        return number[1:]
    elif number.startswith('254'):
        return number
    return '254' + number[-9:]

@login_required
def initiate_payment(request, order_id):
    order = Order.objects.get(order_id=order_id, user=request.user)
    
    if request.method == 'POST':
        raw_phone_number = request.POST.get('phone_number') # <--- Get phone from form
        
        if not raw_phone_number:
            messages.error(request, "Phone number is required.")
            return render(request, 'payment.html', {'order': order})
            
        phone_number = format_phone_number(raw_phone_number)
        
        # Ensure amount is a whole number (integer) as required by M-Pesa
        amount = int(order.total_cost) 
        
        # --- API Call ---
        response_data = initiate_stk_push(phone_number, amount, order.order_id)
        
        # Check M-Pesa Response Code
        if response_data.get('ResponseCode') == '0':
            messages.success(request, 'M-Pesa prompt sent! Check your phone to complete the payment.')
            # You can store CheckoutRequestID here for tracking later
            # order.checkout_request_id = response_data.get('CheckoutRequestID')
            # order.save()
            return redirect('track_order') # Or a confirmation page
        else:
            # Failed to initiate STK Push (e.g., Daraja error, invalid phone format)
            error_message = response_data.get('CustomerMessage', 'Payment initiation failed. Check Daraja logs.')
            messages.error(request, error_message)
            return render(request, 'payment.html', {'order': order})

    # GET Request: Renders the payment form
    return render(request, 'payment.html', {'order': order})

@csrf_exempt 
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Extract relevant payment information from the M-Pesa payload
            result_code = data['Body']['stkCallback']['ResultCode']
            merchant_request_id = data['Body']['stkCallback']['MerchantRequestID']
            checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']

            if result_code == 0:
                # PAYMENT SUCCESSFUL!
                # Extract details (amount, MpesaReceiptNumber, TransactionDate, AccountReference)
                items = data['Body']['stkCallback']['CallbackMetadata']['Item']
                
                # Logic to parse items and update order status in your database
                # (You would use the AccountReference to find the Order model instance)
                # Example: order_id = next(item['Value'] for item in items if item['Name'] == 'AccountReference').split('-')[1]
                
                # 1. Update the Order status to 'Paid'
                # 2. Log the transaction details (receipt number, amount)
                pass 
            else:
                # PAYMENT FAILED or was CANCELLED by the user
                # 1. Update the Order status to 'Payment Failed'
                pass

        except Exception as e:
            # Handle JSON parsing errors or unexpected M-Pesa format
            print(f"Error processing M-Pesa callback: {e}")
            
        # M-Pesa requires a specific success response:
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    
    return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid Method"}, status=405)

@login_required
def history_view(request):
    try:
        user_orders = Order.objects.filter(
            user=request.user
        ).order_by('-order_date') # Sort by newest first
    except NameError:
        # Fallback if the Order model isn't imported or defined yet
        user_orders = [] 
    
    context = {
        'orders': user_orders, # Pass the list of orders to the template
    }
    return render(request, 'history.html', context)

@login_required
def available_vendors(request):
    pending_order_data = request.session.get('pending_order_data', {})
    address = pending_order_data.get('address')

    if not address:
        messages.error(request, "Address not found. Please start the order again.")
        return redirect('orders')

    lng, lat = geocode_address_mapbox(address)
    if not lng or not lat:
        messages.error(request, "Unable to locate your address. Try again.")
        return redirect('orders')

    vendors = find_petrol_stations_mapbox(lng, lat)

    return render(request, 'available_vendors.html', {
    'vendors': json.dumps(vendors),
    'user_lat': float(lat),
    'user_lng': float(lng),
    'mapbox_token': config('MAPBOX_TOKEN'),
})

def geocode_address_mapbox(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {
        'access_token': config ('MAPBOX_TOKEN'),
        'limit': 1,
        'country': 'KE'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Defensive check
        if 'features' in data and data['features']:
            coords = data['features'][0]['geometry']['coordinates']
            return coords[0], coords[1]  # lng, lat
        else:
            print("No features found in Mapbox response:", data)
            return None, None
    except requests.RequestException as e:
        print("Mapbox geocoding request failed:", e)
        return None, None

def find_petrol_stations_mapbox(lng, lat):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/petrol station.json"
    params = {
        'access_token': config ('MAPBOX_TOKEN'),
        'proximity': f"{lng},{lat}",
        'limit': 10,
        'country': 'KE'
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data['features']