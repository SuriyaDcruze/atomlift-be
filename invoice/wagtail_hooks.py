from wagtail import hooks
from wagtail.snippets.widgets import SnippetListingButton
from django.urls import reverse, path
from .models import Invoice
from . import views
import logging

logger = logging.getLogger(__name__)


@hooks.register('register_snippet_listing_buttons')
def add_download_invoice_button(snippet, user, next_url=None):
    """Add 'Download PDF' button in Invoice listing."""
    if isinstance(snippet, Invoice):
        try:
            url = reverse('invoices_invoice:download_invoice_pdf', kwargs={'pk': snippet.pk})
        except Exception as e:
            logger.warning(f"Reverse error: {str(e)}")
            url = f"/admin/snippets/invoice/invoice/download-pdf/{snippet.pk}/"

        return [
            SnippetListingButton(
                label='Download PDF',
                url=url,
                priority=90,
                icon_name='download',
            )
        ]
    return []


@hooks.register('register_admin_urls')
def register_invoice_pdf_url():
    """Register custom PDF download URL."""
    return [
        path(
            'snippets/invoice/invoice/download-pdf/<int:pk>/',
            views.download_invoice_pdf,
            name='download_invoice_pdf'
        ),
    ]
