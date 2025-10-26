from django.urls import path
from . import views

urlpatterns = [
    # Custom delivery challan pages
    path('add/', views.add_delivery_challan_custom, name='add_delivery_challan_custom'),
    path('edit/<str:reference_id>/', views.edit_delivery_challan_custom, name='edit_delivery_challan_custom'),
    
    # API endpoints
    path('api/items/', views.manage_items, name='api_delivery_items'),
    path('api/challan-number/', views.get_next_challan_number, name='api_next_challan_number'),
    path('api/place-of-supply/', views.manage_place_of_supply, name='api_place_of_supply'),
    path('api/place-of-supply/<int:pk>/', views.manage_place_of_supply_detail, name='api_place_of_supply_detail'),
]

