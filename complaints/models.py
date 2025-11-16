from django.db import models
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from django.http import HttpResponseForbidden
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from customer.models import Customer
from authentication.models import CustomUser


# ---------- Dropdown Snippets ----------

class ComplaintType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name


class ComplaintPriority(models.Model):
    name = models.CharField(max_length=20, unique=True)
    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name


# ---------- Main Complaint Model ----------

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    
    reference = models.CharField(max_length=20, unique=True, editable=False)
    complaint_type = models.ForeignKey(ComplaintType, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="complaints")
    contact_person_name = models.CharField(max_length=100, blank=True, null=True)
    contact_person_mobile = models.CharField(max_length=20, blank=True, null=True)
    block_wing = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Lift and Template fields
    lift_info = models.CharField(max_length=200, blank=True, null=True, help_text="Selected lift information")
    complaint_templates = models.TextField(blank=True, null=True, help_text="Selected complaint templates (comma-separated)")

    assign_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'groups__name': 'employee'},
        related_name='assigned_complaints',
    )

    priority = models.ForeignKey(ComplaintPriority, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    technician_remark = models.TextField(blank=True, null=True)
    solution = models.TextField(blank=True, null=True)
    technician_signature = models.ImageField(upload_to='complaints/signatures/', blank=True, null=True, help_text="Technician signature image")
    customer_signature = models.ImageField(upload_to='complaints/signatures/', blank=True, null=True, help_text="Customer signature image")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def save(self, *args, **kwargs):
        if not self.reference:
            last = Complaint.objects.order_by("id").last()
            last_id = 1000
            if last and last.reference.startswith("CMP"):
                try:
                    last_id = int(last.reference.replace("CMP", ""))
                except ValueError:
                    pass
            self.reference = f"CMP{last_id + 1}"

        if self.customer:
            if not self.contact_person_name:
                self.contact_person_name = getattr(self.customer, "contact_person_name", "")
            if not self.contact_person_mobile:
                self.contact_person_mobile = getattr(self.customer, "phone", "")
            if not self.block_wing:
                self.block_wing = getattr(self.customer, "site_address", "")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.subject}"

    complaint_panels = [
        MultiFieldPanel([
            FieldPanel("reference", read_only=True),
            FieldPanel("complaint_type"),
            FieldPanel("date"),
            FieldPanel("priority"),
            FieldPanel("status"),
        ], heading="Complaint Info"),

        MultiFieldPanel([
            FieldPanel("customer"),
            FieldPanel("contact_person_name"),
            FieldPanel("contact_person_mobile"),
            FieldPanel("block_wing"),
            FieldPanel("lift_info"),
            FieldPanel("complaint_templates"),
        ], heading="Customer Details"),

        MultiFieldPanel([
            FieldPanel("assign_to"),
            FieldPanel("subject"),
            FieldPanel("message"),
            FieldPanel("technician_remark"),
            FieldPanel("solution"),
            FieldPanel("technician_signature"),
            FieldPanel("customer_signature"),
        ], heading="Work & Solution Details"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(complaint_panels, heading="Complaint Details"),
    ])


# ---------- Assignment History Model ----------

class ComplaintAssignmentHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="assignment_history")
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments_made")
    assignment_date = models.DateTimeField(default=timezone.now)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assignment_date", "-id"]

class ComplaintCallUpdateHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="call_update_history")
    call_update_date = models.DateTimeField(default=timezone.now)
    attend_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="call_updates_made")
    solution_templates = models.TextField(blank=True, null=True, help_text="Selected solution templates (comma-separated)")
    additional_notes = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-call_update_date", "-id"]

    def __str__(self):
        return f"{self.complaint.reference} - Call Update on {self.call_update_date}"


class ComplaintStatusHistory(models.Model):
    """
    Model to track status changes made through mobile app
    """
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES, blank=True, null=True)
    new_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.TextField(blank=True, null=True, help_text="Reason for status change")
    technician_remark = models.TextField(blank=True, null=True)
    solution = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_from_mobile = models.BooleanField(default=True, help_text="True if changed from mobile app")
    
    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "Status Change History"
        verbose_name_plural = "Status Change Histories"
    
    def __str__(self):
        return f"{self.complaint.reference}: {self.old_status} → {self.new_status}"


# ---------- Wagtail Admin ViewSets ----------

class ComplaintTypeViewSet(SnippetViewSet):
    model = ComplaintType
    icon = "tag"
    menu_label = "Complaint Types"
    list_display = ("name",)


class ComplaintPriorityViewSet(SnippetViewSet):
    model = ComplaintPriority
    icon = "tag"
    menu_label = "Priorities"
    list_display = ("name",)


class ComplaintViewSet(SnippetViewSet):
    model = Complaint
    icon = "info-circle"
    menu_label = "All Complaints"
    inspect_view_enabled = True
    inspect_template_name = 'complaints/view_complaint_custom.html'

    # 👇 Columns shown in list view
    list_display = (
        "reference",
        "customer",
        "subject",
        "status",
        "priority",
        "assign_to",
        "date",
    )
    
    # 👇 Add custom buttons
    list_display_add_buttons = True

    # 👇 Export ALL model fields (CSV + XLSX)
    list_export = [
        "id",
        "reference",
        "complaint_type",
        "date",
        "customer",
        "contact_person_name",
        "contact_person_mobile",
        "block_wing",
        "lift_info",
        "complaint_templates",
        "assign_to",
        "priority",
        "status",
        "subject",
        "message",
        "technician_remark",
        "solution",
        "technician_signature",
        "customer_signature",
        "created",
        "updated",
    ]
    export_formats = ["csv", "xlsx"]

    # 👇 Search fields
    search_fields = (
        "reference",
        "subject",
        "message",
        "customer__site_name",
        "customer__site_id",
        "customer__job_no",
        "contact_person_name",
        "contact_person_mobile",
        "block_wing",
        "lift_info",
        "assign_to__first_name",
        "assign_to__last_name",
        "technician_remark",
        "solution",
    )
    
    # 👇 Filter fields
    list_filter = (
        "status",
        "priority",
        "complaint_type",
        "assign_to",
        "date",
    )

    # Use custom add/edit pages
    def get_add_url(self):
        return reverse("add_complaint_custom")

    def get_edit_url(self, instance):
        return reverse("edit_complaint_custom", args=(instance.reference,))
    
    def get_view_url(self, instance):
        return reverse("view_complaint_custom", args=(instance.reference,))

    def add_view(self, request):
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))
    
    def view_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_view_url(instance))
    
    def inspect_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_view_url(instance))

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            # Check if this is an export request
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                # Only allow superusers to export
                if not request.user.is_superuser:
                    return HttpResponseForbidden("You do not have permission to access this resource.")
            return super().dispatch(request, *args, **kwargs)
    
    index_view_class = RestrictedIndexView



class ComplaintStatusHistoryViewSet(SnippetViewSet):
    model = ComplaintStatusHistory
    icon = "history"
    menu_label = "Status History"
    list_display = ("complaint", "old_status", "new_status", "changed_by", "changed_at", "changed_from_mobile")
    list_filter = ("changed_from_mobile", "new_status", "changed_at")
    search_fields = ("complaint__reference", "complaint__subject", "changed_by__first_name", "changed_by__last_name")
    inspect_view_enabled = True


class ComplaintManagementGroup(SnippetViewSetGroup):
    items = (ComplaintViewSet, ComplaintTypeViewSet, ComplaintPriorityViewSet, ComplaintStatusHistoryViewSet)
    menu_icon = "info-circle"
    menu_label = "Complaints"
    menu_name = "complaints"
    menu_order =8


register_snippet(ComplaintManagementGroup)
