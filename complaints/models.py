from django.db import models
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
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
    reference = models.CharField(max_length=20, unique=True, editable=False)
    complaint_type = models.ForeignKey(ComplaintType, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="complaints")
    contact_person_name = models.CharField(max_length=100, blank=True, null=True)
    contact_person_mobile = models.CharField(max_length=20, blank=True, null=True)
    block_wing = models.CharField(max_length=200, blank=True, null=True)

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
        ], heading="Complaint Info"),

        MultiFieldPanel([
            FieldPanel("customer"),
            FieldPanel("contact_person_name"),
            FieldPanel("contact_person_mobile"),
            FieldPanel("block_wing"),
        ], heading="Customer Details"),

        MultiFieldPanel([
            FieldPanel("assign_to"),
            FieldPanel("subject"),
            FieldPanel("message"),
            FieldPanel("technician_remark"),
            FieldPanel("solution"),
        ], heading="Work & Solution Details"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(complaint_panels, heading="Complaint Details"),
    ])


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

    # 👇 Columns shown in list view
    list_display = (
        "reference",
        "customer",
        "subject",
        "priority",
        "assign_to",
        "date",
    )

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
        "assign_to",
        "priority",
        "subject",
        "message",
        "technician_remark",
        "solution",
        "created",
        "updated",
    ]
    export_formats = ["csv", "xlsx"]

    # 👇 Search fields
    search_fields = (
        "reference",
        "subject",
        "customer__site_name",
        "message",
    )

    # Use custom add/edit pages
    def get_add_url(self):
        return reverse("add_complaint_custom")

    def get_edit_url(self, instance):
        return reverse("edit_complaint_custom", args=(instance.reference,))

    def add_view(self, request):
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))



class ComplaintManagementGroup(SnippetViewSetGroup):
    items = (ComplaintViewSet, ComplaintTypeViewSet, ComplaintPriorityViewSet)
    menu_icon = "info-circle"
    menu_label = "Complaints"
    menu_name = "complaints"
    menu_order = 11 


register_snippet(ComplaintManagementGroup)
