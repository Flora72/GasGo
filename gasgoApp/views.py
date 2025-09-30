import json
from django.http import HttpResponse , JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm # ADDED AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout 

# -------------------------------------
#                   GENERAL VIEWS
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
def dashboard(request):
    return render(request, 'dashboard.html')

# -------------------------------------
#         AUTH RELATED VIEWS
# --------------------------------------
def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        # TODO: Save user to database or create account logic here
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
#         ORDER & VENDOR VIEWS
# --------------------------------------
def order(request):
    return render(request, 'order.html')
def track_order(request):
    return render(request, 'track_order.html')
def vendors(request):
    return render(request, 'vendors.html')
