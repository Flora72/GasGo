import json, requests 
import math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout 
from django.contrib.auth.decorators import login_required
from .models import Order , Profile , Vendor
from .mpesa_integration import initiate_stk_push
from decouple import config
from django.conf import settings
from django.utils.crypto import get_random_string
from django.db.models import F
from django.db.models import FloatField, ExpressionWrapper
from django.http import HttpResponse
from .models import USSDOrder
from django.db.models import Sum, FloatField
from django.db.models.functions import Cast, Replace
from django.db.models import Value
from datetime import datetime
from django.utils import timezone


# -------------------------------------------
# GENERAL VIEWS
# -------------------------------------------
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
    return render(request, 'emergency.html',
                  {'is_dashboard': True,})

@login_required(login_url='login')
def gasbot(request):
    return render(request, 'gasbot.html',{
        'is_dashboard': True,
    })


@login_required
def dashboard(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Calculate Total KG
    total_kg_data = user_orders.annotate(
        clean_size=Replace('size', Value('kg'), Value(''))
    ).annotate(
        size_as_float=Cast('clean_size', FloatField())
    ).aggregate(total=Sum('size_as_float'))
    total_kg = total_kg_data['total'] or 0

    # Dynamic Expected Duration
    prediction_percentage = 0
    show_recommender = False
    days_left = "--"

    if user_orders.count() >= 2:
        # Calculate actual average days between orders
        order_dates = list(user_orders.values_list('created_at', flat=True)[:5])
        intervals = [(order_dates[i] - order_dates[i + 1]).days for i in range(len(order_dates) - 1)]
        avg_duration = sum(intervals) / len(intervals)
        expected_duration = max(avg_duration, 7)
    else:
        # Default for new users
        expected_duration = 30

    last_order = user_orders.first()
    if last_order:
        days_since = (datetime.now().date() - last_order.created_at.date()).days
        # Calculate percentage based on dynamic or default duration
        prediction_percentage = max(0, 100 - (int((days_since / expected_duration) * 100)))
        days_left = max(0, int(expected_duration - days_since))

        # Show recommender naturally if level is low
        if prediction_percentage <= 20:
            show_recommender = True

    context = {
        'total_kg': total_kg,
        'prediction_percentage': prediction_percentage,
        'show_recommender': show_recommender,
        'days_left': days_left,
        'expected_duration': expected_duration,
        'last_order': last_order,
        'is_dashboard': True,
    }
    return render(request, 'dashboard.html', context)
@login_required
def history(request):

    user_orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    context = {
        'orders': user_orders,
        'is_dashboard': True,
    }

    return render(request, 'history.html', context)
# -------------------------------------------
# AUTH RELATED VIEWS
# -------------------------------------------
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
            return render(request, 'signup.html', {
                'alert_message': "Passwords do not match."
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {
                'alert_message': "That username is already taken."
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {
                'alert_message': "An account with that email already exists."
            })

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        user.save()

        request.session['confirm_message'] = "Account created successfully. Do you want to log in now?"
        return redirect('login')

    return render(request, 'signup.html')

def login(request):
    confirm_message = request.session.pop('confirm_message', None)
    alert_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            request.session['alert_message'] = f"Welcome back, {user.username}!"
            return redirect('dashboard')
        else:
            alert_message = "Invalid username or password."

    return render(request, 'login.html', {
        'alert_message': alert_message,
        'confirm_message': confirm_message
    })

def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({"message": "Email is required"}, status=400)

            form = PasswordResetForm({'email': email})

            if form.is_valid():
                form.save(
                    request=request,
                    email_template_name='password_reset_email.txt',
                    from_email='GasGo Assistance <gasgoassistance@gmail.com>',
                    subject_template_name='password_reset_subject.txt',
                )
            return JsonResponse({
                "message": "If the email is registered, a password reset link has been sent."
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid data format"}, status=400)
        except ValidationError:
            pass

   
    return render(request, 'forgot_password.html')

@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Handle profile image upload
    if request.method == 'POST' and 'profile_image' in request.FILES:
        user_profile.profile_image = request.FILES['profile_image']
        user_profile.save()
        return redirect('profile')

    # Get latest pending order
    latest_order = Order.objects.filter(
        user=request.user,
        status='Pending Payment'
    ).order_by('-created_at').first()

    context = {
        'user_profile': user_profile,
        'order': latest_order if latest_order else None
    }
    return render(request, 'profile.html', { 'is_dashboard': True,})

# -------------------------------------------
# ORDERS AND VENDORS RELATED VIEWS
# -------------------------------------------
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders, 'is_dashboard' : True,})

def find_nearest_vendor(lat, lng):
    distance_expr = ExpressionWrapper(
        (F('location_lat') - lat) * (F('location_lat') - lat) +
        (F('location_lng') - lng) * (F('location_lng') - lng),
        output_field=FloatField()
    )
    return Vendor.objects.annotate(distance=distance_expr).order_by('distance').first()

@login_required(login_url='login')
def order(request):
    if request.method == 'POST':
        # 1. Collect Details
        brand_raw = request.POST.get('brand')
        size = request.POST.get('size')
        selected_brand = brand_raw if brand_raw else "TotalEnergies"

        order_details = {
            'size': size,
            'brand': selected_brand,
            'exchange': request.POST.get('exchange'),
            'quantity': request.POST.get('quantity', 1),
            'full_name': request.POST.get('full_name'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'directions': request.POST.get('directions') or "",
            'preferred_time': request.POST.get('preferred_time'),
            'notes': request.POST.get('notes') or "",
        }

        # 2. Handle Geolocation
        try:
            lat_raw = request.POST.get('delivery_latitude')
            lng_raw = request.POST.get('delivery_longitude')
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
            if lat and lng and -90 <= lat <= 90 and -180 <= lng <= 180:
                order_details['delivery_latitude'] = lat
                order_details['delivery_longitude'] = lng
        except (TypeError, ValueError):
            pass

        # 3. Validation
        if not all([order_details['size'], order_details['address'], order_details['phone'], order_details['full_name']]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'order.html', {'is_dashboard': True, 'order_details': order_details})

        # 4. Pricing Logic
        PRICE_MAP = {
            ('ProGas', '6kg'): 1100, ('ProGas', '13kg'): 2500, ('ProGas', '22.5kg'): 4300, ('ProGas', '35kg'): 6700, ('ProGas', '50kg'): 9500,
            ('TotalEnergies', '6kg'): 1050, ('TotalEnergies', '13kg'): 2450, ('TotalEnergies', '22.5kg'): 4200, ('TotalEnergies', '35kg'): 6600, ('TotalEnergies', '50kg'): 9400,
            ('Afri-Gas', '6kg'): 1020, ('Afri-Gas', '13kg'): 2400, ('Afri-Gas', '22.5kg'): 4150, ('Afri-Gas', '35kg'): 6550, ('Afri-Gas', '50kg'): 9300,
            ('K-Gas', '6kg'): 1000, ('K-Gas', '13kg'): 2350, ('K-Gas', '22.5kg'): 4100, ('K-Gas', '35kg'): 6500, ('K-Gas', '50kg'): 9200,
            ('RubisGas', '6kg'): 1030, ('RubisGas', '13kg'): 2420, ('RubisGas', '22.5kg'): 4180, ('RubisGas', '35kg'): 6580, ('RubisGas', '50kg'): 9350,
        }

        # Calculate unit price and store in the dictionary
        price = PRICE_MAP.get((order_details['brand'], order_details['size']), 1050)
        order_details['price'] = price

        # 5. SESSION STORAGE (Crucial Step)
        # We store the dictionary so subsequent views can "pick" the data
        request.session['pending_order_data'] = order_details
        request.session['pending_order_id'] = "GGO-" + get_random_string(10).upper()

        return redirect('available_vendors')

    return render(request, 'order.html', {'is_dashboard': True})
@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.delete()
    return redirect('my_orders')

@login_required(login_url='login')
def confirm_order(request):
    vendor_name = request.POST.get('vendor_choice')
    pending_order_data = request.session.get('pending_order_data')
    print("Session pending_order_data:", request.session.get('pending_order_data'))

    if request.method == 'POST':
        if not pending_order_data:
            messages.error(request, "Session expired or missing order data. Please start again.")
            return redirect('order')

        vendor_name = request.POST.get('vendor_choice')
        notes = request.POST.get('notes', '')

        if not vendor_name:
            messages.error(request, "Please select a vendor to proceed.")
            return redirect('available_vendors')
        try:
            vendor_obj = Vendor.objects.get(name=vendor_name)
        except Vendor.DoesNotExist:
            messages.error(request, "Selected vendor not found. Please try again.")
            return redirect('available_vendors')

        final_order_data = {
            **pending_order_data,
            'vendor': vendor_obj,
            'notes': notes,
            'user': request.user,
            'status': 'Pending'
        }

        try:
            new_order = Order.objects.create(**final_order_data)
            del request.session['pending_order_data']
            messages.success(request, "Order confirmed! Proceed to payment.")
            return redirect('initiate_payment', order_id=new_order.order_id)
        except Exception as e:
            print("Order creation failed:", e)
            messages.error(request, "Something went wrong while confirming your order.")
            return redirect('available_vendors')


    return render(request, 'confirm_order.html', {
        'pending_order': pending_order_data
    })

def is_valid_coord(value):
    try:
        return value is not None and -90 <= float(value) <= 90
    except:
        return False


@login_required
def track_order(request):
    order_id = request.GET.get('order_id')

    if order_id:
        order = Order.objects.filter(order_id=order_id, user=request.user).first()
    else:
        # Get the most recent order for this user
        order = Order.objects.filter(user=request.user).order_by('-created_at').first()

    if not order:
        return render(request, 'track_order.html', {
            'demo_mode': True,
            'google_api_key': config('GOOGLE_MAPS_API_KEY')
        })

    # Ensure these fields match your Model definition exactly
    context = {
        'is_dashboard': True,
        'order': order,
        'rider_lat': order.rider_latitude or None,
        'rider_lng': order.rider_longitude or None,
        'user_lat': order.delivery_latitude,
        'user_lng': order.delivery_longitude,
        'google_api_key': config('GOOGLE_MAPS_API_KEY')
    }
    return render(request, 'track_order.html', context)

@login_required
def vendors(request):
    # Fetch session data at the very start so it's available for all logic paths
    pending_data = request.session.get('pending_order_data', {})
    vendor_session = request.session.get('selected_vendor', {})

    if request.method == 'POST':
        vendor_choice = request.POST.get('vendor_choice')
        vendor_lat = request.POST.get('vendor_lat')
        vendor_lng = request.POST.get('vendor_lng')
        payment_method = request.POST.get('payment_method')
        final_notes = request.POST.get('notes')

        # Handle initial map selection (picking the station)
        if vendor_lat and vendor_lng:
            if not vendor_choice:
                messages.error(request, "Please select a vendor from the map.")
                return redirect('available_vendors')

            # Save selection to session
            vendor_session = {
                'name': vendor_choice,
                'lat': vendor_lat,
                'lng': vendor_lng,
                'notes': final_notes
            }
            request.session['selected_vendor'] = vendor_session

            # Render vendors.html directly to keep 'pending_order_data' in context
            return render(request, 'vendors.html', {
                'is_dashboard': True,
                'vendors': Vendor.objects.all(),
                'selected_vendor': vendor_session,
                'pending_order_data': pending_data
            })

        # Final order processing (User clicked "Confirm Order")
        if not vendor_choice or not payment_method or not pending_data:
            messages.error(request, "Your order session has expired. Please start over.")
            return redirect('order')

        # Get or create the Vendor object for the Database
        selected_vendor, _ = Vendor.objects.get_or_create(
            name=vendor_choice,
            defaults={
                'location_lat': vendor_session.get('lat'),
                'location_lng': vendor_session.get('lng')
            }
        )

        # Dynamic Calculation for the Database entry
        unit_price = float(pending_data.get('price', 0))
        qty = int(pending_data.get('quantity', 1))
        calculated_total = unit_price * qty
        order_id = "GGO-" + get_random_string(10).upper()

        # CREATE THE PERMANENT ORDER
        new_order = Order.objects.create(
            user=request.user,
            vendor=selected_vendor,
            order_id=order_id,
            status='Confirmed' if payment_method == 'Cash' else 'Pending Payment',
            total_cost=calculated_total,
            quantity=qty,
            size=pending_data.get('size'),
            brand=pending_data.get('brand'),
            exchange=pending_data.get('exchange'),
            full_name=pending_data.get('full_name'),
            phone=pending_data.get('phone'),
            address=pending_data.get('address'),

            # COORDINATES SAVED HERE
            delivery_latitude=pending_data.get('delivery_latitude'),
            delivery_longitude=pending_data.get('delivery_longitude'),

            directions=pending_data.get('directions', ""),
            preferred_time=pending_data.get('preferred_time'),
            notes=final_notes or vendor_session.get('notes', ""),
            price=unit_price
        )

        # CLEANUP
        request.session.pop('pending_order_data', None)
        request.session.pop('selected_vendor', None)

        # FINAL REDIRECTS
        if payment_method == 'M-Pesa':
            return redirect('initiate_payment', order_id=new_order.order_id)
        else:
            return render(request, 'confirm_order.html', {
                'order': new_order,
                'is_dashboard': True
            })

    # GET Request: Initial vendor selection state
    return render(request, 'vendors.html', {
        'is_dashboard': True,
        'vendors': Vendor.objects.all(),
        'selected_vendor': vendor_session,
        'pending_order_data': pending_data
    })
@login_required
def available_vendors(request):
    user_lat, user_lng = -1.2921, 36.8219

    order_id = request.session.get('pending_order_id')
    order = Order.objects.filter(order_id=order_id, user=request.user).first()

    if order and order.delivery_latitude and order.delivery_longitude:
        user_lat = order.delivery_latitude
        user_lng = order.delivery_longitude
    else:
        print("No delivery coordinates found. Using fallback.")

    stations = find_petrol_stations_mapbox(user_lng, user_lat)

    formatted_stations = [
        {
            "name": s.get("text", "Unnamed"),
            "address": s.get("place_name", ""),
            "lat": s["geometry"]["coordinates"][1],
            "lng": s["geometry"]["coordinates"][0]
        }
        for s in stations
    ]

    if order and formatted_stations:
        first = formatted_stations[0]
        vendor, _ = Vendor.objects.get_or_create(name=first["name"])
        order.vendor = vendor
        order.rider_latitude = first["lat"]
        order.rider_longitude = first["lng"]
        order.save()

    return render(request, "available_vendors.html", {
        'is_dashboard' : True,
        "user_lat": user_lat,
        "user_lng": user_lng,
        "google_api_key": settings.GOOGLE_MAPS_API_KEY,
        "stations": formatted_stations,
        "order": order
    })


# -------------------------------------------
# PAYMENT RELATED VIEWS
# -------------------------------------------
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
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if request.method == 'POST':
        raw_phone_number = request.POST.get('phone_number')

        if not raw_phone_number:
            messages.error(request, "Phone number is required.")
            return render(request, 'payment.html', {'order': order, 'is_dashboard': True})

        phone_number = format_phone_number(raw_phone_number)
        amount = int(order.total_cost)

        response_data = initiate_stk_push(phone_number, amount, order.order_id)

        if response_data.get('ResponseCode') == '0':
            messages.success(request, 'M-Pesa prompt sent! Check your phone.')
            order.checkout_request_id = response_data.get('CheckoutRequestID')
            order.save()
            return redirect('track_order')
        else:
            error_message = response_data.get('CustomerMessage', 'Payment initiation failed.')
            messages.error(request, error_message)
            return render(request, 'payment.html', {'order': order, 'is_dashboard': True})


    return render(request, 'payment.html', {'order': order, 'is_dashboard': True})

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

                items = data['Body']['stkCallback']['CallbackMetadata']['Item']
                
                pass 
            else:
                
                pass

        except Exception as e:
            
            print(f"Error processing M-Pesa callback: {e}")
            
       
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    
    return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid Method"}, status=405)

# -------------------------------------------
# MAP RELATED VIEWS
# -------------------------------------------
@login_required
def geocode_address_mapbox(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {
        'access_token': config('MAPBOX_TOKEN'),
        'limit': 1,
        'country': 'KE'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]  
    except requests.RequestException as e:
        print("Mapbox geocoding failed:", e)
    return None, None

def find_petrol_stations_mapbox(lng, lat):
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/petrol station.json"
    params = {
        'access_token': config('MAPBOX_TOKEN'),
        'proximity': f"{lng},{lat}",
        'limit': 10,
        'country': 'KE'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('features', [])
    except requests.RequestException as e:
        print("Mapbox station lookup failed:", e)
        return []

# -------------------------------------------
# AFRSTKNG VIEWS
# -------------------------------------------
def ussd_access(request):
    # This renders the page. 
    # 'is_dashboard': False ensures it uses the landing page layout in base.html
    return render(request, 'ussd_access.html', {'is_dashboard': False})

@csrf_exempt
def ussd_callback(request):
    try:
        if request.method == "POST":
            session_id = request.POST.get("sessionId", "")
            phone_number = request.POST.get("phoneNumber", "")
            text = request.POST.get("text", "")

            parts = text.split("*")
            user_input = parts[-1] if text else ""
            
            # 1. Price Map & Helpers
            PRICE_MAP = {
                ('ProGas', '6kg'): 1100, ('ProGas', '13kg'): 2500, ('ProGas', '22.5kg'): 4300, ('ProGas', '35kg'): 6700, ('ProGas', '50kg'): 9500,
                ('TotalEnergies', '6kg'): 1050, ('TotalEnergies', '13kg'): 2450, ('TotalEnergies', '22.5kg'): 4200, ('TotalEnergies', '35kg'): 6600, ('TotalEnergies', '50kg'): 9400,
                ('Afri-Gas', '6kg'): 1020, ('Afri-Gas', '13kg'): 2400, ('Afri-Gas', '22.5kg'): 4150, ('Afri-Gas', '35kg'): 6550, ('Afri-Gas', '50kg'): 9300,
                ('K-Gas', '6kg'): 1000, ('K-Gas', '13kg'): 2350, ('K-Gas', '22.5kg'): 4100, ('K-Gas', '35kg'): 6500, ('K-Gas', '50kg'): 9200,
                ('RubisGas', '6kg'): 1030, ('RubisGas', '13kg'): 2420, ('RubisGas', '22.5kg'): 4180, ('RubisGas', '35kg'): 6580, ('RubisGas', '50kg'): 9350,
            }
            brands = ["ProGas", "TotalEnergies", "Afri-Gas", "K-Gas", "RubisGas"]
            sizes = ["6kg", "13kg", "22.5kg", "35kg", "50kg"]

            # --- USSD MENU NAVIGATION ---
            
            # Step 0: Main Menu
            if text == "":
                response = "CON Welcome to GasGo\n1. Order Gas\n2. Check Order Status"

            # OPTION 1: ORDERING FLOW
            elif text == "1":
                response = "CON Select Brand:\n1. ProGas\n2. TotalEnergies\n3. Afri-Gas\n4. K-Gas\n5. RubisGas"

            elif len(parts) == 2 and parts[0] == "1":
                response = "CON Select Size:\n1. 6kg\n2. 13kg\n3. 22.5kg\n4. 35kg\n5. 50kg"

            elif len(parts) == 3 and parts[0] == "1":
                response = "CON Enter Quantity (e.g., 1):"

            elif len(parts) == 4 and parts[0] == "1":
                response = "CON Enter Delivery Location:"

            elif len(parts) == 5 and parts[0] == "1":
                try:
                    brand = brands[int(parts[1]) - 1]
                    size = sizes[int(parts[2]) - 1]
                    qty = int(parts[3])
                    total = PRICE_MAP.get((brand, size), 0) * qty
                    response = f"CON Confirm Order:\n{qty}x {brand} {size}\nLocation: {parts[4]}\nTotal: KES {total}\n1. Confirm\n2. Cancel"
                except:
                    response = "END Invalid selection. Please try again."

            elif len(parts) == 6 and parts[0] == "1":
                if user_input == "1":
                    # Re-calculate Brand, Size, and Amount for Payment
                    brand = brands[int(parts[1]) - 1]
                    size = sizes[int(parts[2]) - 1]
                    qty = int(parts[3])
                    total_amount = PRICE_MAP.get((brand, size), 0) * qty
                    
                    # 1. Create Order in Database
                    order = USSDOrder.objects.create(
                        session_id=session_id,
                        phone_number=phone_number,
                        gas_size=f"{brand} {size}",
                        quantity=qty,
                        location=parts[4],
                        confirmed=True
                    )
                    
                    # 2. Trigger M-Pesa STK Push
                    # Format phone to 254... format
                    formatted_phone = phone_number.replace("+", "")
                    order_ref = f"GAS{order.id:05d}"
                    
                    try:
                        initiate_stk_push(total_amount, formatted_phone, order_ref)
                        payment_note = "\nPlease enter M-Pesa PIN on the pop-up."
                    except Exception as e:
                        payment_note = "\n(Payment request failed. Our agent will call you.)"

                    response = f"END Order placed! ID: {order_ref}.{payment_note}"
                else:
                    response = "END Order cancelled."

            # OPTION 2: TRACKING FLOW
            elif text == "2":
                order = USSDOrder.objects.filter(phone_number=phone_number).order_by('-created_at').first()
                if not order:
                    response = "END No active orders. Dial *384*93233# to order!"
                else:
                    order_id = f"GAS{order.id:05d}"
                    minutes_passed = (timezone.now() - order.created_at).total_seconds() / 60
                    current_dist = max(0.0, 3.0 - (minutes_passed * 0.5))
                    eta = math.ceil(current_dist * 4)

                    if current_dist == 0:
                        response = f"END Order {order_id}\nStatus: Arrived!\nThe rider is at {order.location}."
                    else:
                        response = f"CON Order {order_id} Tracking\n"
                        response += f"Dist. to Station: {round(current_dist, 1)}km\n"
                        response += f"Est. Arrival: {eta} mins\n"
                        response += f"Location: {order.location}\n\n0. Back"

            elif user_input == "0":
                response = "CON Welcome to GasGo\n1. Order Gas\n2. Check Order Status"
            
            else:
                response = "END Invalid input."

            return HttpResponse(response, content_type='text/plain')

    except Exception as e:
        return HttpResponse(f"END Server Error: {str(e)}", content_type='text/plain')
    try:
        if request.method == "POST":
            session_id = request.POST.get("sessionId", "")
            phone_number = request.POST.get("phoneNumber", "")
            text = request.POST.get("text", "")

            parts = text.split("*")
            user_input = parts[-1] if text else ""
            
            # 1. Price Map & Helper Lists
            PRICE_MAP = {
                ('ProGas', '6kg'): 1100, ('ProGas', '13kg'): 2500, ('ProGas', '22.5kg'): 4300, ('ProGas', '35kg'): 6700, ('ProGas', '50kg'): 9500,
                ('TotalEnergies', '6kg'): 1050, ('TotalEnergies', '13kg'): 2450, ('TotalEnergies', '22.5kg'): 4200, ('TotalEnergies', '35kg'): 6600, ('TotalEnergies', '50kg'): 9400,
                ('Afri-Gas', '6kg'): 1020, ('Afri-Gas', '13kg'): 2400, ('Afri-Gas', '22.5kg'): 4150, ('Afri-Gas', '35kg'): 6550, ('Afri-Gas', '50kg'): 9300,
                ('K-Gas', '6kg'): 1000, ('K-Gas', '13kg'): 2350, ('K-Gas', '22.5kg'): 4100, ('K-Gas', '35kg'): 6500, ('K-Gas', '50kg'): 9200,
                ('RubisGas', '6kg'): 1030, ('RubisGas', '13kg'): 2420, ('RubisGas', '22.5kg'): 4180, ('RubisGas', '35kg'): 6580, ('RubisGas', '50kg'): 9350,
            }
            brands = ["ProGas", "TotalEnergies", "Afri-Gas", "K-Gas", "RubisGas"]
            sizes = ["6kg", "13kg", "22.5kg", "35kg", "50kg"]

            # --- USSD MENU NAVIGATION ---
            
            # Step 0: Main Menu
            if text == "":
                response = "CON Welcome to GasGo\n1. Order Gas\n2. Check Order Status"

            # OPTION 1: ORDERING
            elif text == "1":
                response = "CON Select Brand:\n1. ProGas\n2. TotalEnergies\n3. Afri-Gas\n4. K-Gas\n5. RubisGas"

            elif len(parts) == 2 and parts[0] == "1":
                response = "CON Select Size:\n1. 6kg\n2. 13kg\n3. 22.5kg\n4. 35kg\n5. 50kg"

            elif len(parts) == 3 and parts[0] == "1":
                response = "CON Enter Quantity (e.g., 1):"

            elif len(parts) == 4 and parts[0] == "1":
                response = "CON Enter Delivery Location:"

            elif len(parts) == 5 and parts[0] == "1":
                try:
                    brand = brands[int(parts[1]) - 1]
                    size = sizes[int(parts[2]) - 1]
                    qty = int(parts[3])
                    total = PRICE_MAP.get((brand, size), 0) * qty
                    response = f"CON Confirm Order:\n{qty}x {brand} {size}\nLocation: {parts[4]}\nTotal: KES {total}\n1. Confirm\n2. Cancel"
                except:
                    response = "END Invalid selection. Please try again."

            elif len(parts) == 6 and parts[0] == "1":
                if user_input == "1":
                    brand = brands[int(parts[1]) - 1]
                    size = sizes[int(parts[2]) - 1]
                    order = USSDOrder.objects.create(
                        session_id=session_id, phone_number=phone_number,
                        gas_size=f"{brand} {size}", quantity=int(parts[3]),
                        location=parts[4], confirmed=True
                    )
                    response = f"END Order placed! ID: #GAS{order.id:05d}."
                else:
                    response = "END Order cancelled."

            # OPTION 2: TRACKING
            elif text == "2":
                order = USSDOrder.objects.filter(phone_number=phone_number).order_by('-created_at').first()
                if not order:
                    response = "END No active orders found. Dial *384*93233# to order!"
                else:
                    order_id = f"GAS{order.id:05d}"
                    # Tracking Logic
                    minutes_passed = (timezone.now() - order.created_at).total_seconds() / 60
                    current_dist = max(0.0, 3.0 - (minutes_passed * 0.5))
                    eta = math.ceil(current_dist * 4)

                    if current_dist == 0:
                        response = f"END Order {order_id}\nStatus: Arrived!\nThe rider is at {order.location}."
                    else:
                        response = f"CON Order {order_id} Tracking\n"
                        response += f"Dist. to Station: {round(current_dist, 1)}km\n"
                        response += f"Est. Arrival: {eta} mins\n"
                        response += f"Location: {order.location}\n\n0. Back"

            elif user_input == "0":
                response = "CON Welcome to GasGo\n1. Order Gas\n2. Check Order Status"
            
            else:
                response = "END Invalid input."

            return HttpResponse(response, content_type='text/plain')

    except Exception as e:
        # If the code crashes, this tells you WHY on the USSD screen
        return HttpResponse(f"END Error: {str(e)}", content_type='text/plain')
    if request.method == "POST":
        session_id = request.POST.get("sessionId", "")
        phone_number = request.POST.get("phoneNumber", "")
        text = request.POST.get("text", "")

        parts = text.split("*")
        user_input = parts[-1] if text else ""
        
        # 1. Expanded Price Map
        PRICE_MAP = {
            ('ProGas', '6kg'): 1100, ('ProGas', '13kg'): 2500, ('ProGas', '22.5kg'): 4300, ('ProGas', '35kg'): 6700, ('ProGas', '50kg'): 9500,
            ('TotalEnergies', '6kg'): 1050, ('TotalEnergies', '13kg'): 2450, ('TotalEnergies', '22.5kg'): 4200, ('TotalEnergies', '35kg'): 6600, ('TotalEnergies', '50kg'): 9400,
            ('Afri-Gas', '6kg'): 1020, ('Afri-Gas', '13kg'): 2400, ('Afri-Gas', '22.5kg'): 4150, ('Afri-Gas', '35kg'): 6550, ('Afri-Gas', '50kg'): 9300,
            ('K-Gas', '6kg'): 1000, ('K-Gas', '13kg'): 2350, ('K-Gas', '22.5kg'): 4100, ('K-Gas', '35kg'): 6500, ('K-Gas', '50kg'): 9200,
            ('RubisGas', '6kg'): 1030, ('RubisGas', '13kg'): 2420, ('RubisGas', '22.5kg'): 4180, ('RubisGas', '35kg'): 6580, ('RubisGas', '50kg'): 9350,
        }

        # Shared Helper Lists
        brands = ["ProGas", "TotalEnergies", "Afri-Gas", "K-Gas", "RubisGas"]
        sizes = ["6kg", "13kg", "22.5kg", "35kg", "50kg"]

        # Step 0: Main Menu
        if text == "":
            response = "CON Welcome to GasGo\n1. Order Gas\n2. Check Order Status"

        # Step 1: Select Brand
        elif text == "1":
            response = "CON Select Brand:\n1. ProGas\n2. TotalEnergies\n3. Afri-Gas\n4. K-Gas\n5. RubisGas"

        # Step 2: Select Size (Added 35kg and 50kg to the menu)
        elif len(parts) == 2 and parts[0] == "1":
            response = "CON Select Size:\n1. 6kg\n2. 13kg\n3. 22.5kg\n4. 35kg\n5. 50kg"

        # Step 3: Enter Quantity
        elif len(parts) == 3 and parts[0] == "1":
            response = "CON Enter Quantity (e.g., 1):"

        # Step 4: Enter Location
        elif len(parts) == 4 and parts[0] == "1":
            response = "CON Enter Delivery Location:"

        # Step 5: Confirmation Logic
        elif len(parts) == 5 and parts[0] == "1":
            try:
                brand = brands[int(parts[1]) - 1]
                size = sizes[int(parts[2]) - 1]
                qty = int(parts[3])
                loc = parts[4]
                
                unit_price = PRICE_MAP.get((brand, size), 0)
                total_price = unit_price * qty
                
                response = f"CON Confirm Order:\n{qty}x {brand} {size}\nLocation: {loc}\nTotal: KES {total_price}\n1. Confirm\n2. Cancel"
            except (IndexError, ValueError):
                response = "END Invalid selection. Please restart the process."

        # Step 6: Finalize Order
        elif len(parts) == 6 and parts[0] == "1":
            if user_input == "1":
                brand = brands[int(parts[1]) - 1]
                size = sizes[int(parts[2]) - 1]
                
                order = USSDOrder.objects.create(
                    session_id=session_id,
                    phone_number=phone_number,
                    gas_size=f"{brand} {size}",
                    quantity=int(parts[3]),
                    location=parts[4],
                    confirmed=True
                )
                response = f"END Order placed successfully! ID: #GAS{order.id:05d}. We will call you shortly."
            else:
                response = "END Order cancelled. Thank you for choosing GasGo."

        # Track Order Logic
        elif text == "2":
            # Fetches the absolute latest order made by this phone number
            order = USSDOrder.objects.filter(phone_number=phone_number).order_by('-created_at').first()
            
            if not order:
                response = "END You have no active orders. Dial *384*93233# to order gas!"
            else:
                # 1. Get the ID for display
                order_id = f"GAS{order.id:05d}"
                
                # 2. Calculate time passed (in minutes)
                now = timezone.now()
                minutes_passed = (now - order.created_at).total_seconds() / 60
                
                # 3. SETTINGS FOR YOUR DEMO:
                start_distance = 3.0  # Starting distance from petrol station
                speed_km_per_min = 0.5 # The rider covers 0.5km every minute
                
                # 4. Calculate current distance (Dynamic)
                # It decreases as minutes_passed increases
                current_distance = max(0.0, start_distance - (minutes_passed * speed_km_per_min))
                
                # 5. Calculate ETA using your 1km = 4min rule
                eta = math.ceil(current_distance * 4)

                if current_distance == 0:
                    response = f"END Order {order_id}\nStatus: Arrived!\nThe rider has reached {order.location} with your {order.gas_size} cylinder."
                else:
                    response = f"CON Order {order_id} Tracking\n"
                    response += f"--------------------\n"
                    response += f"Dist. to Station: {round(current_distance, 1)}km\n"
                    response += f"Est. Arrival: {eta} mins\n"
                    response += f"Location: {order.location}\n\n"
                    response += "0. Back"

        elif user_input == "0":
            response = "CON Welcome to GasGo\n1. Order Gas\n2. Check Order Status"