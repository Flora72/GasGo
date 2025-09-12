from tkinter.font import names

from. import views
from django.urls import path

urlpatterns =[
    path('',views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('emergency/', views.emergency, name='emergency'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('track_order/', views.track_order, name='track_order'),
    path('vendors/', views.vendors, name='vendors'),
    path('orders/', views.order, name='orders'),


]