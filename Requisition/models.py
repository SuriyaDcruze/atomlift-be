from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.forms.widgets import RadioSelect

from authentication.models import CustomUser
from items.models import Item
from customer.models import Customer
from amc.models import AMC


# ---------- MAIN MODEL ----------
class Requisition(models.Model):
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    date = models.DateField()
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    qty = models.PositiveIntegerField()
    site = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    amc_id = models.ForeignKey(AMC, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.CharField(max_length=100, blank=True)
    employee = models.ForeignKey(
    CustomUser,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    limit_choices_to={'groups__name': 'employee'},  # ✅ FIXED
    related_name='assigned_requisitions',
     )
    status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('CLOSED', 'Closed'),
        ],
        default='OPEN'
    )
    approve_for = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )

    panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            FieldPanel("date"),
            FieldPanel("item"),
            FieldPanel("qty"),
            FieldPanel("site"),
            FieldPanel("amc_id"),
            FieldPanel("service"),
            FieldPanel("employee"),
        ], heading="Requisition Details"),

        MultiFieldPanel([
            FieldPanel("status", widget=RadioSelect),
            FieldPanel("approve_for", widget=RadioSelect),
        ], heading="Status & Approval"),
    ]

    class Meta:
        verbose_name = "Requisition"
        verbose_name_plural = "Requisitions"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.reference_id:
            last_requisition = Requisition.objects.all().order_by('id').last()
            if last_requisition and last_requisition.reference_id.startswith('REQ'):
                last_id = int(last_requisition.reference_id.replace('REQ', ''))
                self.reference_id = f'REQ{str(last_id + 1).zfill(3)}'
            else:
                self.reference_id = 'REQ001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_id} - {self.item or 'No Item'}"


# ---------- SNIPPET VIEWSET ----------
class RequisitionViewSet(SnippetViewSet):
    model = Requisition
    icon = "form"
    menu_label = "Requisitions"
    inspect_view_enabled = True
    list_display = (
        "reference_id",
        "date",
        "item",
        "qty",
        "site",
        "amc_id",
        "service",
        "employee",
        "status",
        "approve_for",
    )
    search_fields = ("reference_id", "item__name", "site__site_name", "employee__username")
    list_filter = ("status", "approve_for", "date")


# ---------- GROUP ----------
class InventoryGroup(SnippetViewSetGroup):
    items = (RequisitionViewSet,)
    icon = "folder-open-inverse"
    menu_label = "Inventory "
    menu_name = "inventory"


# ---------- REGISTER GROUP ----------
register_snippet(InventoryGroup)
