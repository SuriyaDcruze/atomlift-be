from wagtail import hooks
from django.urls import path
from .views import add_requisition_custom, edit_requisition_custom

@hooks.register('register_admin_urls')
def register_custom_requisition_urls():
    return [
        path('requisition/add-custom/', add_requisition_custom, name='add_requisition_custom'),
        path('requisition/edit-custom/<str:reference_id>/', edit_requisition_custom, name='edit_requisition_custom'),
    ]
