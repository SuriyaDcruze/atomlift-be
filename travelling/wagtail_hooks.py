from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.permissions import ModelPermissionPolicy
from django.urls import reverse
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import TravelRequest
import json

# Custom permission policy to deny add permission
class NoAddTravelRequestPermissionPolicy(ModelPermissionPolicy):
    """Custom permission policy that disallows adding new travel requests"""
    def user_has_permission(self, user, action):
        if action == "add":
            return False
        return super().user_has_permission(user, action)


# Travel Request SnippetViewSet
class TravelRequestViewSet(SnippetViewSet):
    model = TravelRequest
    menu_label = "Travel Requests"
    icon = "globe"
    menu_order = 200
    inspect_view_enabled = True  # Enable Wagtail default inspect view
    create_view_enabled = False  # Disable manual creation
    edit_view_enabled = True  # Allow editing existing requests
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add permission"""
        return NoAddTravelRequestPermissionPolicy(self.model)
    
    list_display = ('travel_date', 'from_place', 'to_place', 'travel_by', 'amount', 'created_by')
    list_filter = ('travel_date', 'travel_by', 'created_by')
    search_fields = ('from_place', 'to_place', 'created_by__username')
    
    list_display_add_buttons = None  # Remove the add button from list view
    list_per_page = 20  # Pagination
    
    def add_view(self, request):
        """Override add view to prevent manual travel request creation"""
        messages.error(
            request, 
            "Travel Requests cannot be created manually. Please edit an existing travel request."
        )
        # Redirect back to the list view using the snippet URL pattern
        return redirect(reverse('snippets:list', args=[self.model._meta.app_label, self.model._meta.model_name]))

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns()
        return urlpatterns

# Travel Request Group
class TravelRequestGroup(SnippetViewSetGroup):
    items = (TravelRequestViewSet,)
    menu_icon = "globe"
    menu_label = "Travel Request"
    menu_name = "travel_request"
    menu_order = 12

# Register the Travel Request group
register_snippet(TravelRequestGroup)

# Hook to remove any add buttons that might appear
@hooks.register('construct_snippet_listing_buttons')
def remove_travel_request_add_buttons(buttons, snippet, user, context=None):
    """Remove any add buttons for TravelRequest"""
    if isinstance(snippet, TravelRequest):
        # Remove any add/create buttons
        buttons[:] = [btn for btn in buttons if not (
            hasattr(btn, 'label') and ('Add' in str(btn.label) or 'Create' in str(btn.label))
        )]
    return buttons

# # Custom menu item for Travel Request frontend
# @hooks.register('register_admin_menu_item')
# def register_travel_request_menu_item():
#     return MenuItem(
#         'Travel Request',
#         reverse('travelling:travel_request_frontend'),
#         icon_name='globe',
#         order=10001
#     )
