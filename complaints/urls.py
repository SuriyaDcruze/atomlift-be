from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom pages
    path('add/', views.add_complaint_custom, name='add_complaint_custom'),
    path('edit/<str:reference>/', views.edit_complaint_custom, name='edit_complaint_custom'),

    # Create/Update endpoints
    path('create/', views.create_complaint, name='create_complaint'),
    path('update/<str:reference>/', views.update_complaint, name='update_complaint'),

    # APIs
    path('api/complaints/customers/', views.get_customers, name='complaints_api_customers'),
    path('api/complaints/types/', views.get_complaint_types, name='complaints_api_types'),
    path('api/complaints/priorities/', views.get_priorities, name='complaints_api_priorities'),
    path('api/complaints/executives/', views.get_executives, name='complaints_api_executives'),
    path('api/complaints/next-reference/', views.get_next_complaint_reference, name='complaints_api_next_reference'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)






