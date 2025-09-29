from django.shortcuts import render
from django.http import HttpResponse , JsonResponse
import json 
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User # Assuming you use the default User model
from django.core.exceptions import ValidationError

# -------------------------------------
#                   GENERAL VIEWS
# --------------------------------------

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def testimonials(request):
    return render(request, 'testimonials.html')

def emergency(request):
    return render(request, 'emergency.html')

def track_order(request):
    return render(request, 'track_order.html')

def vendors(request):
    return render(request, 'vendors.html')

def order(request):
    return render(request, 'order.html')

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')
def gasbot(request):
    return render(request, 'gasbot.html')
def dashboard(request):
    return render(request, 'dashboard.html')
@csrf_exempt
def forgot_password(request):
    """
    Handles both displaying the forgot_password form (GET) 
    and processing the email submission (POST) using Django's built-in flow.
    """
    if request.method == 'POST':
        try:
            # 1. Get the email from the frontend request body
            data = json.loads(request.body) 
            email = data.get('email')

            if not email:
                return JsonResponse({"message": "Email is required"}, status=400)

            # 2. Use Django's PasswordResetForm to handle the logic
            # We must pass the request object so Django can build the correct domain/link
            form = PasswordResetForm({'email': email})

            if form.is_valid():
                # This calls the internal Django logic to:
                # a) Check if the user exists.
                # b) Generate a unique token for the user.
                # c) Send the password reset email using your Brevo settings.
                form.save(
                    request=request, 
                    email_template_name='emails/password_reset_email.html', # We will create this
                    from_email='GasGo Assistance <gasgoassistance@gmail.com>', # Use your verified Brevo sender
                    subject_template_name='emails/password_reset_subject.txt', # We will create this
                )
            
            # 3. Security Best Practice: Always return a generic success message,
            # regardless of whether the email was found, to prevent enumeration attacks.
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