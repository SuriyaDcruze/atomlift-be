from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from django.http import HttpResponseForbidden
from django.forms.widgets import RadioSelect
from django.urls import reverse
from django.shortcuts import redirect

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


# ---------- STOCK REGISTER MODEL ----------
class StockRegister(models.Model):
    """Stock Register to track inventory movements"""
    
    TRANSACTION_CHOICES = [
        ('INWARD', 'Inward'),
        ('OUTWARD', 'Outward'),
    ]
    
    register_no = models.CharField(max_length=10, unique=True, editable=False)
    date = models.DateField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_entries')
    description = models.TextField(blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    inward_qty = models.PositiveIntegerField(default=0, help_text="Quantity received/added to stock")
    outward_qty = models.PositiveIntegerField(default=0, help_text="Quantity issued/removed from stock")
    unit_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Value per unit")
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, editable=False)
    reference = models.CharField(max_length=100, blank=True, help_text="Reference document number")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel("register_no", read_only=True),
            FieldPanel("date"),
            FieldPanel("item"),
            FieldPanel("description"),
        ], heading="Basic Information"),
        
        MultiFieldPanel([
            FieldPanel("transaction_type", widget=RadioSelect),
            FieldPanel("inward_qty"),
            FieldPanel("outward_qty"),
            FieldPanel("unit_value"),
            FieldPanel("reference"),
        ], heading="Transaction Details"),
    ]

    class Meta:
        verbose_name = "Stock Register"
        verbose_name_plural = "Stock Register"
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        # Auto-generate register number
        if not self.register_no:
            last_entry = StockRegister.objects.all().order_by('id').last()
            if last_entry and last_entry.register_no.startswith('STK'):
                last_id = int(last_entry.register_no.replace('STK', ''))
                self.register_no = f'STK{str(last_id + 1).zfill(4)}'
            else:
                self.register_no = 'STK0001'
        
        # Calculate total value
        if self.transaction_type == 'INWARD':
            self.total_value = self.inward_qty * self.unit_value
            self.outward_qty = 0
        else:  # OUTWARD
            self.total_value = self.outward_qty * self.unit_value
            self.inward_qty = 0
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.register_no} - {self.item.name if self.item else 'N/A'} ({self.transaction_type})"

    @staticmethod
    def get_available_stock(item):
        """Calculate available stock for a specific item"""
        entries = StockRegister.objects.filter(item=item)
        total_inward = sum(entry.inward_qty for entry in entries)
        total_outward = sum(entry.outward_qty for entry in entries)
        return total_inward - total_outward


# ---------- SNIPPET VIEWSET ----------
class RequisitionViewSet(SnippetViewSet):
    model = Requisition
    icon = "form"
    menu_label = "Requisitions"
    inspect_view_enabled = True
    

    # ✅ Fields shown in list view
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

    # ✅ Export ALL model fields
    list_export = [
        "id",
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
    ]
    export_formats = ["csv", "xlsx"]

    # ✅ Search and filters
    search_fields = ("reference_id", "item__name", "site__site_name", "employee__username")
    list_filter = ("status", "approve_for", "date")

    def get_add_url(self):
        return reverse("add_requisition_custom")

    def get_edit_url(self, instance):
        return reverse("edit_requisition_custom", args=(instance.reference_id,))

    def add_view(self, request):
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        try:
            instance = self.model.objects.get(pk=pk)
            return redirect(self.get_edit_url(instance))
        except self.model.DoesNotExist:
            from django.shortcuts import render
            return render(request, '404.html', status=404)

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                if not request.user.is_superuser:
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export requisitions.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)

    index_view_class = RestrictedIndexView


# ---------- STOCK REGISTER VIEWSET ----------
class StockRegisterViewSet(SnippetViewSet):
    model = StockRegister
    icon = "doc-full-inverse"
    menu_label = "Stock Register"
    inspect_view_enabled = True
    
    list_display = (
        "register_no",
        "date",
        "item",
        "transaction_type",
        "inward_qty",
        "outward_qty",
        "unit_value",
        "total_value",
        "reference",
    )
    
    list_export = [
        "register_no",
        "date",
        "item",
        "description",
        "transaction_type",
        "inward_qty",
        "outward_qty",
        "unit_value",
        "total_value",
        "reference",
    ]
    
    export_formats = ["csv", "xlsx"]
    
    search_fields = ("register_no", "item__name", "reference", "description")
    list_filter = ("transaction_type", "date", "item__type")

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                if not request.user.is_superuser:
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export stock register.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)

    index_view_class = RestrictedIndexView


# ---------- GROUP ----------
class InventoryGroup(SnippetViewSetGroup):
    items = (RequisitionViewSet, StockRegisterViewSet)
    icon = "folder-open-inverse"
    menu_label = "Inventory "
    menu_name = "inventory"
    menu_order = 12


# ---------- REGISTER GROUP ----------
register_snippet(InventoryGroup)
