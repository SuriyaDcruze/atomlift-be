from django.urls import path
from . import views

urlpatterns = [
    # Custom add/edit pages
    path('add-custom/', views.add_requisition_custom, name='add_requisition_custom'),
    path('edit-custom/<str:reference_id>/', views.edit_requisition_custom, name='edit_requisition_custom'),
    
    # API endpoints
    path('api/requisition/next-reference/', views.get_next_requisition_reference, name='get_next_requisition_reference'),
    path('api/requisition/customers/', views.get_customers, name='get_requisition_customers'),
    
    # Stock Register
    path('stock-register/', views.stock_register_view, name='stock_register'),
]











