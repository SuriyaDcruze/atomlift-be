from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom pages
    path('add/', views.add_complaint_custom, name='add_complaint_custom'),
    path('edit/<str:reference>/', views.edit_complaint_custom, name='edit_complaint_custom'),
    path('view/<str:reference>/', views.view_complaint_custom, name='view_complaint_custom'),

    # Create/Update endpoints
    path('create/', views.create_complaint, name='create_complaint'),
    path('update/<str:reference>/', views.update_complaint, name='update_complaint'),

    # QR Code & Public Complaint
    path('qr/<int:customer_id>/', views.generate_customer_complaint_qr, name='generate_complaint_qr'),
    path('public/<int:customer_id>/', views.public_complaint_form, name='public_complaint_form'),
    path('public/<int:customer_id>/submit/', views.submit_public_complaint, name='submit_public_complaint'),

    # APIs
    path('api/complaints/customers/', views.get_customers, name='complaints_api_customers'),
    path('api/complaints/types/', views.get_complaint_types, name='complaints_api_types'),
    path('api/complaints/priorities/', views.get_priorities, name='complaints_api_priorities'),
    path('api/complaints/executives/', views.get_executives, name='complaints_api_executives'),
    path('api/complaints/next-reference/', views.get_next_complaint_reference, name='complaints_api_next_reference'),
    
    # Mobile App APIs (Simplified - Only 3 endpoints needed)
    path('api/mobile/complaints/', views.mobile_complaints_api, name='mobile_complaints_api'),
    path('api/mobile/complaints/<str:reference>/', views.mobile_complaint_detail_api, name='mobile_complaint_detail_api'),
    path('api/mobile/complaints/<str:reference>/update/', views.mobile_complaint_update_api, name='mobile_complaint_update_api'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)







