from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('add/', views.add_payment_received_custom, name='add_payment_received_custom'),
    path('edit/<str:payment_number>/', views.edit_payment_received_custom, name='edit_payment_received_custom'),

    path('create/', views.create_payment_received, name='create_payment_received'),
    path('update/<str:payment_number>/', views.update_payment_received, name='update_payment_received'),

    path('api/payments/customers/', views.get_customers, name='payments_api_customers'),
    path('api/payments/invoices/', views.get_invoices, name='payments_api_invoices'),
    path('api/payments/next-number/', views.get_next_payment_number, name='payments_api_next_number'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



