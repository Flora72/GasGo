from django.shortcuts import render

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
