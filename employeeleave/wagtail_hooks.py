from wagtail_modeladmin.options import ModelAdmin, modeladmin_register
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils import timezone
from .models import LeaveRequest


class LeaveRequestAdmin(ModelAdmin):
    model = LeaveRequest
    menu_label = "Leave Requests"
    menu_icon = "date"  # Using date icon for leave requests
    menu_order = 202  # After User Profiles (201)
    add_to_settings_menu = True  # Add to Settings menu
    exclude_from_explorer = False
    
    # Responsive list display - optimized columns
    list_display = (
        "get_user_info",
        "get_user_leave_counts",
        "get_leave_details",
        "get_dates",
        "get_reason",
        "get_status_badge",
        "get_admin_remarks",
        "created_at",
    )
    
    # Proper Wagtail admin filters - will display in sidebar like default Wagtail admin
    list_filter = (
        "status",
        "leave_type",
        "half_day",
        "user",
        "from_date",
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
    
    # Custom display methods for responsive layout
    def get_user_info(self, obj):
        """Display user information in a compact, responsive format"""
        user = obj.user
        full_name = user.get_full_name() or user.email
        email = user.email
        
        # Responsive HTML with proper styling
        return format_html(
            '<div class="leave-user-info">'
            '<strong class="user-name">{}</strong><br>'
            '<span class="user-email">{}</span>'
            '</div>',
            full_name,
            email
        )
    get_user_info.short_description = "Employee"
    get_user_info.admin_order_field = "user__first_name"
    
    def get_user_leave_counts(self, obj):
        """Display total leave counts for the user"""
        from django.db.models import Count, Q
        from .models import LeaveRequest
        
        user = obj.user
        counts = LeaveRequest.objects.filter(user=user).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected')),
        )
        
        total = counts['total'] or 0
        pending = counts['pending'] or 0
        approved = counts['approved'] or 0
        rejected = counts['rejected'] or 0
        
        return format_html(
            '<div class="leave-counts" style="font-size: 12px; line-height: 1.6;">'
            '<div><strong>Total:</strong> {}</div>'
            '<div style="color: #ff9800;"><strong>Pending:</strong> {}</div>'
            '<div style="color: #4caf50;"><strong>Approved:</strong> {}</div>'
            '<div style="color: #f44336;"><strong>Rejected:</strong> {}</div>'
            '</div>',
            total,
            pending,
            approved,
            rejected
        )
    get_user_leave_counts.short_description = "Leave Counts"
    get_user_leave_counts.admin_order_field = "user"
    
    def get_leave_details(self, obj):
        """Display leave type and half day indicator"""
        leave_type_display = obj.get_leave_type_display()
        half_day_indicator = ""
        if obj.half_day:
            half_day_indicator = format_html(
                '<span class="half-day-badge" style="'
                'display: inline-block; '
                'background-color: #ff9800; '
                'color: white; '
                'padding: 2px 8px; '
                'border-radius: 12px; '
                'font-size: 11px; '
                'margin-left: 8px;'
                '">Half Day</span>'
            )
        
        return format_html(
            '<div class="leave-type">{}{}</div>',
            leave_type_display,
            half_day_indicator
        )
    get_leave_details.short_description = "Leave Type"
    get_leave_details.admin_order_field = "leave_type"
    
    def get_dates(self, obj):
        """Display date range in a compact format"""
        if obj.from_date == obj.to_date:
            date_str = obj.from_date.strftime("%b %d, %Y")
        else:
            date_str = f"{obj.from_date.strftime('%b %d')} - {obj.to_date.strftime('%b %d, %Y')}"
        
        return format_html(
            '<div class="leave-dates">{}</div>',
            date_str
        )
    get_dates.short_description = "Dates"
    get_dates.admin_order_field = "from_date"
    
    def get_reason(self, obj):
        """Display reason with truncation for responsive view"""
        if obj.reason:
            reason = obj.reason
            if len(reason) > 60:
                reason = reason[:60] + "..."
            return format_html(
                '<div class="leave-reason" title="{}" style="'
                'max-width: 200px; '
                'font-size: 12px; '
                'color: #555;'
                '">{}</div>',
                obj.reason,
                reason
            )
        return format_html('<span style="color: #999;">—</span>')
    get_reason.short_description = "Reason"
    get_reason.admin_order_field = "reason"
    
    def get_status_badge(self, obj):
        """Display status with color-coded badge"""
        status = obj.status
        status_display = obj.get_status_display()
        
        # Color coding for different statuses
        color_map = {
            'pending': '#ff9800',  # Orange
            'approved': '#4caf50',  # Green
            'rejected': '#f44336',  # Red
        }
        bg_color = color_map.get(status, '#757575')  # Default gray
        
        return format_html(
            '<span class="status-badge" style="'
            'display: inline-block; '
            'background-color: {}; '
            'color: white; '
            'padding: 4px 12px; '
            'border-radius: 12px; '
            'font-size: 12px; '
            'font-weight: 500;'
            '">{}</span>',
            bg_color,
            status_display
        )
    get_status_badge.short_description = "Status"
    get_status_badge.admin_order_field = "status"
    
    def get_admin_remarks(self, obj):
        """Display admin remarks with truncation for responsive view"""
        if obj.admin_remarks:
            remarks = obj.admin_remarks
            if len(remarks) > 50:
                remarks = remarks[:50] + "..."
            return format_html(
                '<div class="admin-remarks" title="{}">{}</div>',
                obj.admin_remarks,
                remarks
            )
        return format_html('<span style="color: #999;">—</span>')
    get_admin_remarks.short_description = "Admin Remarks"
    get_admin_remarks.admin_order_field = "admin_remarks"
    
    def created_at(self, obj):
        """Display formatted creation date"""
        if obj.created_at:
            now = timezone.now()
            diff = now - obj.created_at
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes} min ago"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return obj.created_at.strftime("%b %d, %Y")
        return "—"
    created_at.short_description = "Created"
    created_at.admin_order_field = "created_at"


# Register LeaveRequest in Wagtail Admin Settings
modeladmin_register(LeaveRequestAdmin)


# Add custom CSS for responsive design
from wagtail import hooks
from django.utils.html import format_html

@hooks.register('insert_global_admin_css')
def leave_request_admin_css():
    """Add custom CSS for responsive leave request admin"""
    # Use format_html with escaped curly braces
    css_content = """
    <style>
    /* Responsive Leave Request Admin Styles */
    @media screen and (max-width: 768px) {{
        .modeladmin-index .listing {{
            overflow-x: auto;
        }}
        
        .modeladmin-index table {{
            min-width: 600px;
        }}
        
        .leave-user-info {{
            min-width: 150px;
        }}
        
        .leave-type {{
            white-space: nowrap;
        }}
        
        .leave-dates {{
            white-space: nowrap;
            font-size: 13px;
        }}
        
        .status-badge {{
            display: inline-block !important;
        }}
        
        .admin-remarks {{
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
    }}
    
    /* Desktop and Tablet Styles */
    .leave-user-info {{
        line-height: 1.4;
    }}
    
    .leave-user-info .user-name {{
        display: block;
        font-size: 14px;
        color: #333;
    }}
    
    .leave-user-info .user-email {{
        display: block;
        font-size: 12px;
        color: #666;
        margin-top: 2px;
    }}
    
    .leave-type {{
        font-weight: 500;
        color: #333;
    }}
    
    .half-day-badge {{
        vertical-align: middle;
    }}
    
    .leave-dates {{
        font-size: 13px;
        color: #555;
    }}
    
    .status-badge {{
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
        .admin-remarks {{
            font-size: 12px;
            color: #666;
            max-width: 250px;
        }}
        
        .leave-reason {{
            font-size: 12px;
            color: #555;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        /* Filter Sidebar Responsive */
    @media screen and (max-width: 1024px) {{
        .modeladmin-index .sidebar {{
            width: 100%;
            margin-top: 20px;
        }}
        
        .modeladmin-index .listing {{
            width: 100%;
        }}
    }}
    
    /* Table row hover effect */
    .modeladmin-index table tbody tr:hover {{
        background-color: #f5f5f5;
    }}
    
    /* Better spacing in filter sidebar */
    .filter-section {{
        margin-bottom: 20px;
    }}
    </style>
    """
    return format_html(css_content)

