# wagtail_hooks.py - Register custom invoice URLs with Wagtail admin
from wagtail import hooks
from django.urls import path
from .views import add_invoice_custom, edit_invoice_custom

@hooks.register('register_admin_urls')
def register_custom_invoice_urls():
    return [
        path('invoices/add-custom/', add_invoice_custom, name='add_invoice_custom'),
        path('invoices/edit-custom/<str:reference_id>/', edit_invoice_custom, name='edit_invoice_custom'),
    ]