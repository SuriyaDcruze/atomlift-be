from wagtail import hooks
from wagtail.snippets.widgets import SnippetListingButton
from django.urls import reverse, path
from .models import Complaint
from . import views
import logging

logger = logging.getLogger(__name__)


@hooks.register('register_snippet_listing_buttons')
def add_complaint_buttons(snippet, user, next_url=None):
    """Add custom buttons in Complaint listing."""
    if isinstance(snippet, Complaint):
        buttons = []
        
        # Add View Eye Button
        try:
            view_url = reverse('view_complaint_custom', kwargs={'reference': snippet.reference})
            buttons.append(
                SnippetListingButton(
                    label='👁️ View',
                    url=view_url,
                    priority=100,
                    icon_name='view',
                )
            )
        except Exception as e:
            logger.warning(f"View button reverse error: {str(e)}")
        
        # Add Download PDF Button
        try:
            pdf_url = reverse('complaints_complaint:download_complaint_pdf', kwargs={'pk': snippet.pk})
        except Exception as e:
            logger.warning(f"PDF button reverse error: {str(e)}")
            pdf_url = f"/admin/snippets/complaints/complaint/download-pdf/{snippet.pk}/"

        buttons.append(
            SnippetListingButton(
                label='Download PDF',
                url=pdf_url,
                priority=90,
                icon_name='download',
            )
        )
        
        return buttons
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
