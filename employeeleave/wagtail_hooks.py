from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.permissions import ModelPermissionPolicy
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from .models import LeaveRequest


# Custom permission policy to deny add permission
class NoAddLeaveRequestPermissionPolicy(ModelPermissionPolicy):
    """Custom permission policy that disallows adding new leave requests"""
    def user_has_permission(self, user, action):
        if action == "add":
            return False
        return super().user_has_permission(user, action)


class LeaveRequestViewSet(SnippetViewSet):
    model = LeaveRequest
    icon = "date"
    menu_label = "Leave Requests"
    menu_order = 202
    add_to_settings_menu = True  # Add to Settings menu (like Users)
    inspect_view_enabled = True  # Enable Wagtail default inspect view
    create_view_enabled = False  # Disable manual creation - leave requests can only be created via mobile app API
    edit_view_enabled = True  # Allow editing existing requests
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add permission"""
        return NoAddLeaveRequestPermissionPolicy(self.model)
    
    # Standard list display using model fields
    list_display = (
        "id",
        "user",
        "leave_type",
        "from_date",
        "to_date",
        "status",
        "reason",
        "created_at",
    )
    
    search_fields = (
        "id",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "email",
        "leave_type",
        "status",
        "reason",
        "admin_remarks"
    )
    
    # Filter options
    list_filter = (
        "status",
        "leave_type",
        "half_day",
        "user",
        "from_date",
        "to_date",
        "created_at",
    )
    
    list_display_add_buttons = None  # Remove the add button from list view
    list_per_page = 20  # Pagination
    
    # Enable export for better data management
    list_export = [
        "user",
        "leave_type",
        "from_date",
        "to_date",
        "half_day",
        "status",
        "reason",
        "email",
        "admin_remarks",
        "created_at",
    ]
    export_formats = ["csv", "xlsx"]
    
    def list_view(self, request):
        """Override list_view to conditionally disable exports for non-admin users"""
        if not request.user.is_superuser:
            original_export_formats = self.export_formats
            self.export_formats = []
            response = super().list_view(request)
            self.export_formats = original_export_formats
            return response
        return super().list_view(request)
    
    def add_view(self, request):
        """Override add view to prevent manual leave request creation"""
        messages.error(
            request, 
            "Leave Requests cannot be created manually. They can only be created through the mobile app. "
            "Please edit an existing leave request or ask the employee to submit a request via the mobile app."
        )
        # Redirect back to the list view using the snippet URL pattern
        from django.urls import reverse
        return redirect(reverse('snippets:list', args=[self.model._meta.app_label, self.model._meta.model_name]))


# Create a group for Leave Requests (not needed for settings menu, but kept for consistency)
class LeaveRequestGroup(SnippetViewSetGroup):
    items = (LeaveRequestViewSet,)
    menu_icon = "date"
    menu_label = "Leave Requests"
    menu_name = "leave_requests"
    menu_order = 13

# Register the Leave Request ViewSet (will appear in Settings menu due to add_to_settings_menu = True)
register_snippet(LeaveRequestViewSet)

# Hook to remove any add buttons that might appear
@hooks.register('construct_snippet_listing_buttons')
def remove_leave_request_add_buttons(buttons, snippet, user, context=None):
    """Remove any add buttons for LeaveRequest"""
    if isinstance(snippet, LeaveRequest):
        # Remove any add/create buttons
        buttons[:] = [btn for btn in buttons if not (
            hasattr(btn, 'label') and ('Add' in str(btn.label) or 'Create' in str(btn.label))
        )]
    return buttons



