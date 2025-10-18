from wagtail import hooks
from wagtail.snippets.widgets import SnippetListingButton
from django.urls import reverse, path
from .models import Complaint
from . import views
import logging

logger = logging.getLogger(__name__)


@hooks.register('register_snippet_listing_buttons')
def add_download_complaint_button(snippet, user, next_url=None):
    """Add 'Download PDF' button in Complaint listing."""
    if isinstance(snippet, Complaint):
        try:
            url = reverse('complaints_complaint:download_complaint_pdf', kwargs={'pk': snippet.pk})
        except Exception as e:
            logger.warning(f"Reverse error: {str(e)}")
            url = f"/admin/snippets/complaints/complaint/download-pdf/{snippet.pk}/"

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
def register_complaint_pdf_url():
    """Register custom PDF download URL."""
    return [
        path(
            'snippets/complaints/complaint/download-pdf/<int:pk>/',
            views.download_complaint_pdf,
            name='download_complaint_pdf'
        ),
    ]
