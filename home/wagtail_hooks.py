from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from wagtail.admin.ui.components import Component
from django.template.loader import render_to_string
from customer.models import Customer
from complaints.models import Complaint
from amc.models import AMC
from invoice.models import Invoice
from PaymentReceived.models import PaymentReceived
from customer.models import CustomerGroup
from Quotation.models import QuotationGroup
from PaymentReceived.models import PaymentGroup
from invoice.models import InvoiceGroup
from recurringInvoice.models import RecurringInvoiceGroup



@hooks.register('construct_main_menu')
def hide_explorer_menu_item_from_frank(request, menu_items):
    new_menu_items = []
    for item in menu_items:
        # Hide default Wagtail items (including Wagtail's built-in reports)
        if item.name in ['help','explorer','documents','images','reports']:
            continue
        # Hide individual sales groups that are now part of Sales group
        if item.name in ['customer', 'quotation', 'payment', 'invoicing', 'recurring_billing']:
            continue
        new_menu_items.append(item)
    menu_items[:] = new_menu_items



@hooks.register('construct_settings_menu')
def hide_settings_items(request, menu_items):

    new_menu_items = []
    for item in menu_items:
        if not item.name in ['redirects','sites','collections','workflows','workflow-tasks']:
            new_menu_items.append(item)
    menu_items[:] = new_menu_items


@hooks.register('register_admin_menu_item')
def register_main_admin_menu_item():
    return MenuItem(
        'Dashboard',
        reverse('wagtailadmin_home'),
        icon_name='home',
        order=1
    )


# ======================================================
#  SALES GROUP
# ======================================================

class SalesGroup(SnippetViewSetGroup):
    items = (
        CustomerGroup,
        QuotationGroup,
        PaymentGroup,
        InvoiceGroup,
        RecurringInvoiceGroup,
    )
    menu_icon = "tag"
    menu_label = "Sales"
    menu_name = "sales"
    menu_order = 6


# Register the Sales group
register_snippet(SalesGroup)
