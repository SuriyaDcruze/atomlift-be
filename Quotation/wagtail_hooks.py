# wagtail_hooks.py - Register custom quotation URLs with Wagtail admin
from wagtail import hooks
from wagtail.snippets.widgets import SnippetListingButton
from django.urls import path, reverse
from .views import add_quotation_custom, edit_quotation_custom
from .models import Quotation


@hooks.register('register_admin_urls')
def register_custom_quotation_urls():
    return [
        path('quotations/add-custom/', add_quotation_custom, name='add_quotation_custom'),
        path('quotations/edit-custom/<str:reference_id>/', edit_quotation_custom, name='edit_quotation_custom'),
    ]

@hooks.register('register_snippet_listing_buttons')
def add_quotation_buttons(snippet, user, next_url=None):
    """Add custom buttons in Quotation listing."""
    if isinstance(snippet, Quotation):
        buttons = []
        
        # Add Download PDF Button
        try:
            pdf_url = reverse('download_quotation_pdf', kwargs={'pk': snippet.pk})
            buttons.append(
                SnippetListingButton(
                    label='Download PDF',
                    url=pdf_url,
                    priority=90,
                    icon_name='download',
                )
            )
        except Exception as e:
            pass
        
        # Add Email Button (only if customer has email)
        if snippet.customer and snippet.customer.email:
            try:
                email_url = reverse('send_quotation_email', kwargs={'pk': snippet.pk})
                buttons.append(
                    SnippetListingButton(
                        label='Email PDF',
                        url=email_url,
                        priority=85,
                        icon_name='mail',
                    )
                )
            except Exception as e:
                pass
        
        return buttons
    return []

