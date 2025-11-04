from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.permissions import ModelPermissionPolicy
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from .models import AttendanceRecord


# Custom permission policy to deny add permission
class NoAddAttendanceRecordPermissionPolicy(ModelPermissionPolicy):
    """Custom permission policy that disallows adding new attendance records"""
    def user_has_permission(self, user, action):
        if action == "add":
            return False
        return super().user_has_permission(user, action)


class AttendanceRecordViewSet(SnippetViewSet):
    model = AttendanceRecord
    icon = "time"
    menu_label = "Attendance Records"
    menu_order = 203
    add_to_settings_menu = True  # Add to Settings menu (like Users)
    inspect_view_enabled = True  # Enable Wagtail default inspect view
    create_view_enabled = False  # Disable manual creation - attendance records can only be created via mobile app API
    edit_view_enabled = True  # Allow editing existing records
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add permission"""
        return NoAddAttendanceRecordPermissionPolicy(self.model)
    
    # Standard list display using model fields
    list_display = [
        "id",
        "user",
        "check_in_date",
        "check_in_time",
        "check_out_date",
        "check_out_time",
        "is_checked_in",
        "is_checked_out",
    ]
    
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "check_in_location",
        "check_in_note",
        "check_out_location",
        "check_out_note",
    )
    
    # Filter options
    list_filter = (
        "check_in_date",
        "is_checked_in",
        "is_checked_out",
    )
    
    list_display_add_buttons = None  # Remove the add button from list view
    list_per_page = 20  # Pagination
    
    # Enable export for better data management
    list_export = [
        "user",
        "check_in_date",
        "check_in_time",
        "check_in_location",
        "check_in_note",
        "check_out_date",
        "check_out_time",
        "check_out_location",
        "check_out_note",
        "is_checked_in",
        "is_checked_out",
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
        """Override add view to prevent manual attendance record creation"""
        messages.error(
            request, 
            "Attendance Records cannot be created manually. They can only be created through the mobile app. "
            "Please edit an existing attendance record or ask the employee to check in via the mobile app."
        )
        # Redirect back to the list view using the snippet URL pattern
        from django.urls import reverse
        return redirect(reverse('snippets:list', args=[self.model._meta.app_label, self.model._meta.model_name]))


# Create a group for Attendance Records (not needed for settings menu, but kept for consistency)
class AttendanceRecordGroup(SnippetViewSetGroup):
    items = (AttendanceRecordViewSet,)
    menu_icon = "time"
    menu_label = "Attendance Records"
    menu_name = "attendance_records"
    menu_order = 13

# Register the Attendance Record ViewSet (will appear in Settings menu due to add_to_settings_menu = True)
register_snippet(AttendanceRecordViewSet)

# Hook to remove any add buttons that might appear
@hooks.register('construct_snippet_listing_buttons')
def remove_attendance_record_add_buttons(buttons, snippet, user, context=None):
    """Remove any add buttons for AttendanceRecord"""
    if isinstance(snippet, AttendanceRecord):
        # Remove any add/create buttons
        buttons[:] = [btn for btn in buttons if not (
            hasattr(btn, 'label') and ('Add' in str(btn.label) or 'Create' in str(btn.label))
        )]
    return buttons

