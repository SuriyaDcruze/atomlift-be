from django.urls import path
from django.shortcuts import redirect
from . import views

def redirect_to_stock_register_admin(request):
    """Redirect old stock register URL to Wagtail admin"""
    return redirect('/admin/snippets/Requisition/stockregister/')

urlpatterns = [
    # Custom add/edit pages
    path('add-custom/', views.add_requisition_custom, name='add_requisition_custom'),
    path('edit-custom/<str:reference_id>/', views.edit_requisition_custom, name='edit_requisition_custom'),
    
    # API endpoints
    path('api/requisition/next-reference/', views.get_next_requisition_reference, name='get_next_requisition_reference'),
    path('api/requisition/customers/', views.get_customers, name='get_requisition_customers'),
    path('api/requisition/users/', views.get_users, name='get_requisition_users'),
    
    # Stock Register - redirect old URL to Wagtail admin
    path('stock-register/', redirect_to_stock_register_admin, name='stock_register'),
    path('add-stock-register-custom/', views.add_stock_register_custom, name='add_stock_register_custom'),
    path('edit-stock-register-custom/<str:register_no>/', views.edit_stock_register_custom, name='edit_stock_register_custom'),
    path('api/stock-register/next-reference/', views.get_next_stock_register_reference, name='get_next_stock_register_reference'),
]











