from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom quotation pages
    path('add/', views.add_quotation_custom, name='add_quotation_custom'),
    path('edit/<str:reference_id>/', views.edit_quotation_custom, name='edit_quotation_custom'),
    
    # Quotation CRUD operations
    path('create/', views.create_quotation, name='create_quotation'),
    path('update/<str:reference_id>/', views.update_quotation, name='update_quotation'),
    
    # API endpoints for dropdown management
    path('api/customers/', views.get_customers, name='api_get_customers'),
    path('api/amc-types/', views.get_amc_types, name='api_get_amc_types'),
    path('api/executives/', views.get_executives, name='api_get_executives'),
    path('api/lifts/', views.get_lifts, name='api_get_lifts'),
    path('api/lifts-by-customer/', views.get_lifts_by_customer, name='api_get_lifts_by_customer'),
    path('api/quotations/', views.get_quotations, name='api_get_quotations'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
