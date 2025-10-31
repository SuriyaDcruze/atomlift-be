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
    path('api/complaints/update-status/<str:reference>/', views.update_complaint_status, name='complaints_api_update_status'),

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
    path('api/complaints/assigned/', views.get_assigned_complaints, name='complaints_api_assigned'),

    # Quick create/update/delete endpoints for Type and Priority (for + icon)
    path('api/complaints/types/create/', views.create_complaint_type, name='complaints_api_types_create'),
    path('api/complaints/types/<int:pk>/update/', views.update_complaint_type, name='complaints_api_types_update'),
    path('api/complaints/types/<int:pk>/delete/', views.delete_complaint_type, name='complaints_api_types_delete'),

    path('api/complaints/priorities/create/', views.create_complaint_priority, name='complaints_api_priorities_create'),
    path('api/complaints/priorities/<int:pk>/update/', views.update_complaint_priority, name='complaints_api_priorities_update'),
    path('api/complaints/priorities/<int:pk>/delete/', views.delete_complaint_priority, name='complaints_api_priorities_delete'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
