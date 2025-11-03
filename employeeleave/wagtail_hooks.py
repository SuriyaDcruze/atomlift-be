from wagtail_modeladmin.options import ModelAdmin, modeladmin_register
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.html import format_html
from django.utils import timezone
from wagtail import hooks
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
        "get_from_date",
        "get_to_date",
        "get_reason",
        "get_status_badge",
        "get_admin_remarks",
        "created_at",
    )
    
    # Filters removed as per requirement
    # list_filter = (
    #     "status",
    #     "leave_type",
    #     "half_day",
    #     "user",
    #     "from_date",
    #     "created_at",
    # )
    
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
    
    def edit_view(self, request, instance_pk):
        """Override edit view to use custom template with status update capability"""
        leave_request = get_object_or_404(LeaveRequest, pk=instance_pk)
        
        # Handle POST request for status update
        if request.method == 'POST':
            old_status = leave_request.status
            new_status = request.POST.get('status')
            admin_remarks = request.POST.get('admin_remarks', '')
            
            # Validate status
            valid_statuses = ['pending', 'approved', 'rejected']
            if new_status and new_status in valid_statuses:
                # Update status and admin remarks
                leave_request.status = new_status
                leave_request.admin_remarks = admin_remarks
                leave_request.save()
                
                # Email will be sent automatically via the signal (send_leave_status_email_signal)
                
                # Show success message
                if old_status != new_status:
                    messages.success(
                        request,
                        f"Leave request status updated to '{leave_request.get_status_display()}' successfully. "
                        f"Email notification has been sent to the employee."
                    )
                else:
                    messages.success(request, "Leave request updated successfully.")
                
                # Redirect to prevent resubmission - redirect back to the same edit page
                return redirect(request.path)
            else:
                messages.error(request, "Invalid status value.")
        
        context = {
            'leave_request': leave_request,
        }
        return render(request, 'employeeleave/view_leave_request_custom.html', context)
    
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
            '<div class="leave-counts">'
            '<div><strong>Total:</strong> {}</div>'
            '<div><strong>Pending:</strong> {}</div>'
            '<div><strong>Approved:</strong> {}</div>'
            '<div><strong>Rejected:</strong> {}</div>'
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
                '<span class="half-day-badge">Half Day</span>'
            )
        
        return format_html(
            '<div class="leave-type">{}{}</div>',
            leave_type_display,
            half_day_indicator
        )
    get_leave_details.short_description = "Leave Type"
    get_leave_details.admin_order_field = "leave_type"
    
    def get_from_date(self, obj):
        """Display from date"""
        if obj.from_date:
            date_str = obj.from_date.strftime("%b %d, %Y")
            return format_html(
                '<div class="leave-date">{}</div>',
                date_str
            )
        return format_html('<span>—</span>')
    get_from_date.short_description = "From Date"
    get_from_date.admin_order_field = "from_date"
    
    def get_to_date(self, obj):
        """Display to date"""
        if obj.to_date:
            date_str = obj.to_date.strftime("%b %d, %Y")
            return format_html(
                '<div class="leave-date">{}</div>',
                date_str
            )
        return format_html('<span>—</span>')
    get_to_date.short_description = "To Date"
    get_to_date.admin_order_field = "to_date"
    
    def get_reason(self, obj):
        """Display reason with truncation for responsive view"""
        if obj.reason:
            reason = obj.reason
            if len(reason) > 60:
                reason = reason[:60] + "..."
            return format_html(
                '<div class="leave-reason" title="{}">{}</div>',
                obj.reason,
                reason
            )
        return format_html('<span>—</span>')
    get_reason.short_description = "Reason"
    get_reason.admin_order_field = "reason"
    
    def get_status_badge(self, obj):
        """Display status with color-coded badge"""
        status = obj.status
        status_display = obj.get_status_display()

        return format_html(
            '<span class="status-badge status-{}">{}</span>',
            status,
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
        return format_html('<span>—</span>')
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


# Register custom CSS for leave request admin styling
@hooks.register('insert_global_admin_css')
def global_admin_css():
    """Add custom CSS for leave request admin styling"""
    return """
    <link rel="stylesheet" href="/static/employeeleave/css/employeeleave.css">
    """


# Custom filter functionality removed as per requirement
