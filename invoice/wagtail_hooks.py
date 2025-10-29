# wagtail_hooks.py - Register custom invoice URLs with Wagtail admin
from wagtail import hooks
from wagtail.snippets.widgets import SnippetListingButton
from django.urls import path, reverse
from .views import add_invoice_custom, edit_invoice_custom, view_invoice_custom
from .models import Invoice

@hooks.register('register_admin_urls')
def register_custom_invoice_urls():
    return [
        path('invoices/add-custom/', add_invoice_custom, name='add_invoice_custom'),
        path('invoices/edit-custom/<str:reference_id>/', edit_invoice_custom, name='edit_invoice_custom'),
        path('invoices/view-custom/<str:reference_id>/', view_invoice_custom, name='view_invoice_custom'),
    ]

@hooks.register('register_snippet_listing_buttons')
def add_invoice_buttons(snippet, user, next_url=None):
    """Add custom buttons in Invoice listing."""
    if isinstance(snippet, Invoice):
        buttons = []
        
        # Add View Button
        try:
            view_url = reverse('view_invoice_custom', kwargs={'reference_id': snippet.reference_id})
            buttons.append(
                SnippetListingButton(
                    label='👁️ View',
                    url=view_url,
                    priority=100,
                    icon_name='view',
                )
            )
        except Exception as e:
            pass
        
        # Add Download PDF Button
        try:
            pdf_url = reverse('download_invoice_pdf', kwargs={'pk': snippet.pk})
            buttons.append(
                SnippetListingButton(
                    label='📄 Download PDF',
                    url=pdf_url,
                    priority=90,
                    icon_name='download',
                )
            )
        except Exception as e:
            pass
        
        return buttons
    return []