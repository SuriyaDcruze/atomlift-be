from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom recurring invoice pages
    path('add/', views.add_recurring_invoice_custom, name='add_recurring_invoice_custom'),
    path('edit/<str:reference_id>/', views.edit_recurring_invoice_custom, name='edit_recurring_invoice_custom'),
    
    # Recurring invoice CRUD operations
    path('create/', views.create_recurring_invoice, name='create_recurring_invoice'),
    path('update/<str:reference_id>/', views.update_recurring_invoice, name='update_recurring_invoice'),
    
    # API endpoints for dropdown management
    path('api/customers/', views.get_customers, name='recurring_invoice_api_customers'),
    path('api/sales-persons/', views.get_sales_persons, name='recurring_invoice_api_sales_persons'),
    path('api/recurring-invoices/', views.get_recurring_invoices, name='recurring_invoice_api_recurring_invoices'),
    path('api/items/', views.get_items, name='recurring_invoice_api_items'),
    path('api/recurring-invoice-items/<str:reference_id>/', views.get_recurring_invoice_items, name='recurring_invoice_api_items_by_ref'),
    
    # Renewal API endpoints
    path('api/renewal-status/<str:reference_id>/', views.get_renewal_status, name='recurring_invoice_api_renewal_status'),
    path('api/renew/<str:reference_id>/', views.renew_recurring_invoice, name='recurring_invoice_api_renew'),
    
    # Test endpoint
    path('test-renewal/', views.test_renewal, name='test_renewal'),
    
    # Direct renewal endpoint
    path('renewal/<str:reference_id>/', views.renew_recurring_invoice_direct, name='renew_recurring_invoice_direct'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)









