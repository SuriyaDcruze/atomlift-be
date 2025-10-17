from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem


@hooks.register('register_admin_menu_item')
def register_reports_menu():
    """Register Reports menu in Wagtail admin"""
    submenu = Menu(items=[
        MenuItem(
            'Complaints Report',
            reverse('reports:complaints_report'),
            icon_name='doc-full-inverse',
            order=100
        ),
        MenuItem(
            'Invoice Report',
            reverse('reports:invoice_report'),
            icon_name='doc-full-inverse',
            order=200
        ),
        MenuItem(
            'Payment Report',
            reverse('reports:payment_report'),
            icon_name='doc-full-inverse',
            order=300
        ),
        MenuItem(
            'Quotation Report',
            reverse('reports:quotation_report'),
            icon_name='doc-full-inverse',
            order=400
        ),
        MenuItem(
            'Routine Service Report',
            reverse('reports:routine_service_report'),
            icon_name='doc-full-inverse',
            order=500
        ),
    ])
    
    return SubmenuMenuItem(
        'Reports',
        submenu,
        icon_name='folder-open-inverse',
        order=10000
    )