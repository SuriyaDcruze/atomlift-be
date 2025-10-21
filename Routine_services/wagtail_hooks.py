from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem

@hooks.register('register_admin_menu_item')
def register_routine_serrvices_menu():
    """Register Routine Services menu in Wagtail admin"""
    submenu = Menu(items=[
        MenuItem(
            'All Routine Services',
            reverse('routine_services:routine_services'),
            icon_name='doc-full-inverse',
            order=100
        ),
        MenuItem(
            'Today\'s Services',
            reverse('routine_services:today_routine_services'),
            icon_name='doc-full-inverse',
            order=200
        ),
        MenuItem(
            'Route Wise Services',
            reverse('routine_services:route_wise_services'),
            icon_name='doc-full-inverse',
            order=300
        ),
        MenuItem(
            'This Month Services',
            reverse('routine_services:this_month_services'),
            icon_name='doc-full-inverse',
            order=400
        ),
        MenuItem(
            'Last Month Overdue',
            reverse('routine_services:last_month_overdue'),
            icon_name='doc-full-inverse',
            order=500
        ),
        MenuItem(
            'This Month Overdue',
            reverse('routine_services:this_month_overdue'),
            icon_name='doc-full-inverse',
            order=600
        ),
        MenuItem(
            'This Month Completed',
            reverse('routine_services:this_month_completed'),
            icon_name='doc-full-inverse',
            order=700
        ),
        MenuItem(
            'Last Month Completed',
            reverse('routine_services:last_month_completed'),
            icon_name='doc-full-inverse',
            order=800
        ),
        MenuItem(
            'Pending Services',
            reverse('routine_services:pending_services'),
            icon_name='doc-full-inverse',
            order=900
        )
    ])

    return SubmenuMenuItem(
        'Routine Services',
        submenu,
        name='routine_services',
        icon_name='cog',
        order=7
    )
