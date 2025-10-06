from . import views
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('emergency/', views.emergency, name='emergency'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('profile/', views.profile, name='profile'),
    path('history/', views.history, name='history'),
    path('track_order/', views.track_order, name='track_order'),
    path('vendors/', views.vendors, name='vendors'),
    path('orders/', views.order, name='orders'),
    path('gasbot/', views.gasbot, name='gasbot'),
    path('history/', views.history_view, name='history'), 
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='reset_password.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),  name='password_reset_complete'),
    path('payment/<str:order_id>/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/', views.payment, name='payment'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]