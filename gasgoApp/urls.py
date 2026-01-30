from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

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

    # password reset flow
    path('forgot_password/', auth_views.PasswordResetView.as_view(
        template_name='forgot_password.html',
        email_template_name='password_reset_email.txt',
        subject_template_name='password_reset_subject.txt',
        success_url='/password_reset_done/'
    ), name='forgot_password'),

    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),

    # changed from /reset/... to /newpassword/...
    path('newpassword/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='new_password.html',
        success_url='/newpassword/done/'
    ), name='password_reset_confirm'),

    path('newpassword/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),

    path('profile/', views.profile, name='profile'),
    path('history/', views.history, name='history'),
    path('track_order/', views.track_order, name='track_order'),
    path('confirm_order/', views.confirm_order, name='confirm_order'),
    path('vendors/', views.vendors, name='vendors'),
    path('orders/', views.order, name='orders'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('vendors/available/', views.available_vendors, name='available_vendors'),
    path('gasbot/', views.gasbot, name='gasbot'),
    path('payment/<str:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('ussd/', views.ussd_callback, name='ussd_callback'),
    path('ussd-access/', views.ussd_access, name='ussd_access'),
]

