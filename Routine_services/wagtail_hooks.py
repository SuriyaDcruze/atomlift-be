from wagtail import hooks


# Hide Routine Service expiring viewsets from main menu (they're in Snippets menu)
@hooks.register('construct_main_menu')
def hide_routine_service_expiring_menu_items(request, menu_items):
    """Hide Routine Service expiring menu items from the admin menu (they're in Snippets)"""
    # Hidden menu labels for Routine Service expiring viewsets
    hidden_labels = [
        'This Month Expiring',
        'Last Month Expired',
        'Routine Services Expiring'
    ]
    
    new_menu_items = []
    for item in menu_items:
        # Check if this is a group and filter its submenu items
        if hasattr(item, 'menu_items') and item.menu_items:
            # Filter submenu items
            filtered_submenu = []
            for sub_item in item.menu_items:
                # Check by label or name
                item_label = getattr(sub_item, 'label', '') or getattr(sub_item, 'name', '')
                if item_label not in hidden_labels:
                    filtered_submenu.append(sub_item)
            # Update the submenu if it changed
            if len(filtered_submenu) != len(item.menu_items):
                item.menu_items = filtered_submenu
        # Check if this item itself should be hidden
        item_label = getattr(item, 'label', '') or getattr(item, 'name', '')
        if item_label not in hidden_labels:
            new_menu_items.append(item)
    menu_items[:] = new_menu_items