from wagtail_modeladmin.options import ModelAdmin, modeladmin_register
from django.contrib import messages
from django.shortcuts import redirect
from .models import LeaveRequest


class LeaveRequestAdmin(ModelAdmin):
    model = LeaveRequest
    menu_label = "Leave Requests"
    menu_icon = "date"  # Using date icon for leave requests
    menu_order = 202  # After User Profiles (201)
    add_to_settings_menu = True  # Add to Settings menu
    exclude_from_explorer = False
    
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
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "reason",
        "admin_remarks"
    )
    
    list_display_add_buttons = None  # Remove the add button from list view
    list_per_page = 20  # Pagination
    ordering = ["-created_at"]  # Show newest first
    
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
    
    # Disable the ability to create new leave requests manually
    # Leave requests can only be created via mobile app API
    def get_permission_helper_class(self):
        """Override permission helper to disable 'add' permission"""
        from wagtail_modeladmin.helpers import PermissionHelper
        
        class LeaveRequestPermissionHelper(PermissionHelper):
            def user_can_create(self, user):
                """Disable manual leave request creation - leave requests can only be created via mobile app"""
                return False
        
        return LeaveRequestPermissionHelper
    
    def create_view(self, request):
        """Override create view to prevent manual leave request creation"""
        messages.error(
            request, 
            "Leave Requests cannot be created manually. They can only be created through the mobile app. "
            "Please edit an existing leave request or ask the employee to submit a request via the mobile app."
        )
        # Redirect back to the list view
        return redirect(self.url_helper.index_url)


# Register LeaveRequest in Wagtail Admin Settings
modeladmin_register(LeaveRequestAdmin)



