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



@hooks.register('construct_main_menu')
def hide_explorer_menu_item_from_frank(request, menu_items):
    new_menu_items = []
    for item in menu_items:
        if not item.name in ['help','explorer','documents','images']:
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
