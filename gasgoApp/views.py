import json, requests
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
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import USSDOrder

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
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                auth_login(request, user)
                request.session['alert_message'] = f"Welcome back, {user.username}!"
                return redirect('dashboard')
            else:
                alert_message = "Invalid username or password."
        else:
            alert_message = "Invalid username or password."

    form = AuthenticationForm()
    return render(request, 'login.html', {
        'form': form,
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
                    email_template_name='emails/password_reset_email.html',
                    from_email='GasGo Assistance <gasgoassistance@gmail.com>',
                    subject_template_name='emails/password_reset_subject.txt',
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
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})

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

        
        try:
            lat = float(request.POST.get('delivery_latitude'))
            lng = float(request.POST.get('delivery_longitude'))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                order_details['delivery_latitude'] = lat
                order_details['delivery_longitude'] = lng
            else:
                lat = lng = None
        except (TypeError, ValueError):
            lat = lng = None

        
        if not order_details['size'] or not order_details['address'] or not order_details['phone']:
            messages.error(request, "Please fill in all required fields (Size, Address, Phone).")
            return render(request, 'order.html', {'order_details': order_details})

        
        order_id = "GGO-" + get_random_string(10).upper()
        new_order = Order.objects.create(
            user=request.user,
            order_id=order_id,
            status='Pending',
            **order_details
        )

        
        if lat is not None and lng is not None:
            vendor = find_nearest_vendor(lat, lng)
            if vendor:
                new_order.vendor = vendor
                new_order.rider_latitude = vendor.location_lat
                new_order.rider_longitude = vendor.location_lng
                new_order.save()

        print(f"New order {order_id} placed with location: {lat}, {lng}")
        request.session['pending_order_id'] = new_order.order_id
        messages.success(request, f"Order placed! Your tracking ID is {new_order.order_id}")
        return redirect('available_vendors')

    return render(request, 'order.html')

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.delete()
    return redirect('my_orders')

@login_required(login_url='login')
def confirm_order(request):
    if request.method == 'POST':
        
        pending_order_data = request.session.get('pending_order_data')
        if not pending_order_data:
            messages.error(request, "Session expired or missing order data. Please start again.")
            return redirect('order')

        
        vendor_name = request.POST.get('vendor_choice')
        notes = request.POST.get('notes', '')

        if not vendor_name:
            messages.error(request, "Please select a vendor to proceed.")
            return redirect('available_vendors')

        final_order_data = {
            **pending_order_data,
            'vendor': vendor_name,
            'notes': notes,
            'user': request.user,
            'status': 'Pending'
        }

    
        try:
            new_order = Order.objects.create(**final_order_data)
            del request.session['pending_order_data']
            messages.success(request, "Order confirmed! Proceed to payment.")
            return redirect('payment', order_id=new_order.id)
        except Exception as e:
            print("Order creation failed:", e)
            messages.error(request, "Something went wrong while confirming your order.")
            return redirect('available_vendors')

   
    return redirect('order')


def is_valid_coord(value):
    try:
        return value is not None and -90 <= float(value) <= 90
    except:
        return False

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
            'google_api_key': config('GOOGLE_MAPS_API_KEY')
        })

    rider_lat = float(order.rider_latitude) if is_valid_coord(order.rider_latitude) else None
    rider_lng = float(order.rider_longitude) if is_valid_coord(order.rider_longitude) else None
    user_lat = float(order.delivery_latitude) if is_valid_coord(order.delivery_latitude) else None
    user_lng = float(order.delivery_longitude) if is_valid_coord(order.delivery_longitude) else None

    context = {
        'order': order,
        'demo_mode': False,
        'tracking_mode': tracking_mode,
        'rider_lat': rider_lat,
        'rider_lng': rider_lng,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'google_api_key': config('GOOGLE_MAPS_API_KEY')
    }
    return render(request, 'track_order.html', context)

@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

   
    if request.method == 'POST' and 'profile_image' in request.FILES:
        user_profile.profile_image = request.FILES['profile_image']
        user_profile.save()
        return redirect('profile')

    
    latest_order = Order.objects.filter(
        user=request.user,
        status='Pending Payment'
    ).order_by('-created_at').first()

    context = {
        'user_profile': user_profile,
        'order': latest_order 
    }
    return render(request, 'profile.html', context)

def history(request):
    return render(request, 'history.html')

@login_required 
def vendors(request):
    if request.method == 'POST':
        
        if 'vendor_lat' in request.POST and 'vendor_lng' in request.POST:
            vendor_choice = request.POST.get('vendor_choice')
            vendor_lat = request.POST.get('vendor_lat')
            vendor_lng = request.POST.get('vendor_lng')
            final_notes = request.POST.get('notes')

            if not vendor_choice:
                messages.error(request, "Please select a vendor.")
                return redirect('available_vendors')

            
            request.session['selected_vendor'] = {
                'name': vendor_choice,
                'lat': vendor_lat,
                'lng': vendor_lng,
                'notes': final_notes
            }

            return redirect('vendors')

        vendor_choice = request.POST.get('vendor_choice')
        payment_method = request.POST.get('payment_method')
        final_notes = request.POST.get('notes')
        pending_order_data = request.session.get('pending_order_data', {})
        vendor_data = request.session.get('selected_vendor', {})

        if not vendor_choice or not payment_method or not pending_order_data or not vendor_data:
            messages.error(request, "Missing vendor or payment details. Please try again.")
            return redirect('available_vendors')

        selected_vendor, _ = Vendor.objects.get_or_create(
            name=vendor_choice,
            defaults={
                'location_lat': vendor_data.get('lat'),
                'location_lng': vendor_data.get('lng')
            }
        )

        total_cost = 3200.00
        new_order = Order.objects.create(
            user=request.user,
            vendor=selected_vendor,
            status='Pending Payment',
            total_cost=total_cost,
            notes=final_notes or vendor_data.get('notes'),
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

        request.session.pop('pending_order_data', None)
        request.session.pop('selected_vendor', None)

        if payment_method == 'M-Pesa':
            return render(request, 'payment.html', {'order': new_order})
        else:
            new_order.status = 'Confirmed'
            new_order.save()
            return render(request, 'confirm_order.html', {'order': new_order})

  
    vendors = Vendor.objects.all()
    return render(request, 'vendors.html', {'vendors': vendors})


    if request.method == 'POST':
        vendor_choice = request.POST.get('vendor_choice')
        vendor_lat = request.POST.get('vendor_lat')  
        vendor_lng = request.POST.get('vendor_lng')
        payment_method = request.POST.get('payment_method')
        final_notes = request.POST.get('notes')
        pending_order_data = request.session.get('pending_order_data', {})

        if not vendor_choice or not payment_method or not pending_order_data:
            messages.error(request, "Vendor or payment method missing. Please try again.")
            return redirect('available_vendors')

        selected_vendor, _ = Vendor.objects.get_or_create(
            name=vendor_choice,
            defaults={
                'location_lat': vendor_lat,
                'location_lng': vendor_lng
            }
        )

        total_cost = 3200.00
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

        request.session.pop('pending_order_data', None)

        if payment_method == 'M-Pesa':
            return render(request, 'payment.html', {'order': new_order})
        else:
            new_order.status = 'Confirmed'
            new_order.save()
            return render(request, 'confirm_order.html', {'order': new_order})

    vendors = Vendor.objects.all()
    return render(request, 'vendors.html', {'vendors': vendors})

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
        raw_phone_number = request.POST.get('phone_number') 
        
        if not raw_phone_number:
            messages.error(request, "Phone number is required.")
            return render(request, 'payment.html', {'order': order})
            
        phone_number = format_phone_number(raw_phone_number)
        
        
        amount = int(order.total_cost) 
        
        
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

                items = data['Body']['stkCallback']['CallbackMetadata']['Item']
                
                pass 
            else:
                
                pass

        except Exception as e:
            
            print(f"Error processing M-Pesa callback: {e}")
            
       
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    
    return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid Method"}, status=405)

@login_required
def history_view(request):
    try:
        user_orders = Order.objects.filter(
            user=request.user
        ).order_by('-order_date')
    except NameError:
        user_orders = [] 
    
    context = {
        'orders': user_orders,
    }
    return render(request, 'history.html', context)


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
        "user_lat": user_lat,
        "user_lng": user_lng,
        "google_api_key": settings.GOOGLE_MAPS_API_KEY,
        "stations": formatted_stations
    })



def ussd_access(request):
    return render(request, 'ussd_access.html')

@csrf_exempt
def ussd_callback(request):
    if request.method == "POST":
        text = request.POST.get("text", "")
        session_id = request.POST.get("sessionId", "")
        phone_number = request.POST.get("phoneNumber", "")

        parts = text.split("*")
        if len(parts) >= 4:
            gas_size = parts[1]
            quantity = parts[2]
            location = parts[3]
            confirmed = parts[4] == "1"

            order = USSDOrder.objects.create(
                session_id=session_id,
                phone_number=phone_number,
                gas_size=gas_size,
                quantity=int(quantity),
                location=location,
                confirmed=confirmed
            )
            return HttpResponse(f"#GAS{order.id:05d}")
        return HttpResponse("Invalid USSD input")
    return HttpResponse("Only POST allowed")
