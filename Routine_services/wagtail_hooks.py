from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem


@hooks.register('register_admin_menu_item')
def register_routine_services_menu():
    """Register Routine Services menu in Wagtail admin"""
    
    menu_items = []
    
    # Define routine services page models and their display names
    services_configs = [
        ('Routine_services.AllRoutineServicesPage', 'All Routine Services', 100),
        ('Routine_services.TodayServicesPage', 'Today\'s Services', 200),
        ('Routine_services.RouteWiseServicesPage', 'Route Wise Services', 300),
        ('Routine_services.ThisMonthServicesPage', 'This Month Services', 400),
        ('Routine_services.LastMonthOverduePage', 'Last Month Overdue', 500),
        ('Routine_services.ThisMonthOverduePage', 'This Month Overdue', 600),
        ('Routine_services.ThisMonthCompletedPage', 'This Month Completed', 700),
        ('Routine_services.LastMonthCompletedPage', 'Last Month Completed', 800),
        ('Routine_services.PendingServicesPage', 'Pending Services', 900),
    ]
    
    # Create menu items for each service page
    for model_string, title, order_num in services_configs:
        try:
            from django.apps import apps
            page_model = apps.get_model(model_string)
            
            # Get the first live instance of this page type
            page = page_model.objects.live().first()
            
            if page:
                menu_items.append(
                    MenuItem(
                        title,
                        page.get_url(),
                        icon_name='doc-full-inverse',
                        order=order_num
                    )
                )
        except Exception:
            # If page doesn't exist yet, skip it
            pass
    
    # Always create submenu even if empty (for debugging)
    if not menu_items:
        # Fallback: show a link to setup pages
        menu_items.append(
            MenuItem(
                'Setup Routine Services',
                '/admin/pages/',
                icon_name='warning',
                order=1
            )
        )
    
    return SubmenuMenuItem(
        'Routine Services',
        Menu(items=menu_items),
        icon_name='cog',
        order=7
    )
