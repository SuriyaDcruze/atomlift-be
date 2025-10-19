# wagtail_hooks.py (corrected to include custom URL registration and remove unnecessary JS since it's handled in custom template)
from wagtail import hooks
from django.urls import path
from .views import add_item_custom, edit_item_custom

@hooks.register('register_admin_urls')
def register_custom_item_urls():
    return [
        path('items/add-custom/', add_item_custom, name='add_item_custom'),
        path('items/edit-custom/<str:item_number>/', edit_item_custom, name='edit_item_custom'),
    ]