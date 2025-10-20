from django.urls import path
from . import views

urlpatterns = [
    # Custom invoice pages
    path('add/', views.add_invoice_custom, name='add_invoice_custom'),
    path('edit/<str:reference_id>/', views.edit_invoice_custom, name='edit_invoice_custom'),
    
    # API endpoints for dropdown management
    path('api/customers/', views.manage_customers, name='api_manage_customers'),
    path('api/customers/<int:pk>/', views.manage_customers_detail, name='api_manage_customers_detail'),
    path('api/amc-types/', views.manage_amc_types, name='api_manage_amc_types'),
    path('api/amc-types/<int:pk>/', views.manage_amc_types_detail, name='api_manage_amc_types_detail'),
    path('api/items/', views.manage_items, name='api_manage_items'),
    
    # PDF download
    path('pdf/<int:pk>/', views.download_invoice_pdf, name='download_invoice_pdf'),
]
