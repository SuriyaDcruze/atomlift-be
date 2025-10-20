# wagtail_hooks.py (corrected to include custom URL registration and remove unnecessary JS since it's handled in custom template)
from wagtail import hooks
from django.urls import path
from .views import add_item_custom, edit_item_custom, manage_types, manage_types_detail, manage_makes, manage_makes_detail, manage_units, manage_units_detail

@hooks.register('register_admin_urls')
def register_custom_item_urls():
    return [
        path('items/add-custom/', add_item_custom, name='add_item_custom'),
        path('items/edit-custom/<str:item_number>/', edit_item_custom, name='edit_item_custom'),
        # Admin APIs for Types/Makes/Units (add/edit/delete)
        path('api/items/types/', manage_types, name='api_items_types'),
        path('api/items/types/<int:pk>/', manage_types_detail, name='api_items_types_detail'),
        path('api/items/makes/', manage_makes, name='api_items_makes'),
        path('api/items/makes/<int:pk>/', manage_makes_detail, name='api_items_makes_detail'),
        path('api/items/units/', manage_units, name='api_items_units'),
        path('api/items/units/<int:pk>/', manage_units_detail, name='api_items_units_detail'),
    ]