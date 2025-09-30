from django.shortcuts import render
from django.http import HttpResponse

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
def forgot_password(request):
    return render(request, 'forgot_password.html')