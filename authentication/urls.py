from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Mobile App Authentication APIs
    path('api/mobile/generate-otp/', views.generate_otp, name='generate_otp'),
    path('api/mobile/verify-otp/', views.verify_otp_and_login, name='verify_otp'),
    path('api/mobile/login/', views.email_password_login, name='email_password_login'),
    path('api/mobile/resend-otp/', views.resend_otp, name='resend_otp'),
    path('api/mobile/logout/', views.logout, name='logout'),
    path('api/mobile/user-details/', views.get_user_details, name='get_user_details'),
]
