from django.db import models
from django.urls import reverse
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import IndexView
from django.http import HttpResponseForbidden
from modelcluster.models import ClusterableModel
from authentication.models import CustomUser  # Corrected import

# Assuming the following models exist in these respective apps:
# Customer in 'customer' app
# AMCType in 'amc' app
# CustomUser and Lift in 'authentication' app

class Quotation(ClusterableModel):
    REFERENCE_PREFIX = 'ALQ'
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    
    # Corrected Lazy References for cross-app relationships
    customer = models.ForeignKey(
        'customer.Customer', on_delete=models.SET_NULL, null=True, blank=True
    )
    amc_type = models.ForeignKey(
        'amc.AMCType', on_delete=models.SET_NULL, null=True, blank=True
     )
    
    sales_service_executive = models.ForeignKey(
    CustomUser,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    limit_choices_to={'groups__name': 'employee'},  # ✅ FIXED
    related_name='assigned_quotations',
    )

    lifts = models.ManyToManyField(
        'lift.Lift', 
        blank=True,
        help_text="Select one or more lifts associated with this quotation"
    )
    
    QUOTATION_TYPE_CHOICES = [
        ('Parts/Peripheral Quotation', 'Parts/Peripheral Quotation'),
        ('Repair', 'Repair'),
        ('AMC Renewal Quotation', 'AMC Renewal Quotation'),
        ('AMC', 'AMC')
    ]
    type = models.CharField(
        max_length=50,
        choices=QUOTATION_TYPE_CHOICES,
        default='Parts/Peripheral Quotation',
        verbose_name="Quotation Type"
    )
    
    year_of_make = models.CharField(max_length=4, blank=True)
    date = models.DateField(auto_now_add=True)  # This is the problematic field
    remark = models.TextField(blank=True)
    other_remark = models.TextField(blank=True)
    uploads_files = models.FileField(upload_to='quotation_uploads/', null=True, blank=True, max_length=100)

    # Wagtail Admin Panels
    panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            FieldPanel("customer"),
            FieldPanel("type"),
            FieldPanel("amc_type"),
            FieldPanel("sales_service_executive"),
            FieldPanel("year_of_make"),
            
            # 💡 FIX: Mark 'date' as read_only because auto_now_add=True makes it non-editable
            FieldPanel("date", read_only=True), 
            
        ], heading="Quotation Details"),
        
        MultiFieldPanel([
            FieldPanel("lifts"),
        ], heading="Associated Lifts"),
        
        MultiFieldPanel([
            FieldPanel("remark"),
            FieldPanel("other_remark"),
            FieldPanel("uploads_files"),
        ], heading="Remarks & Attachments"),
    ]

    class Meta:
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"

    def save(self, *args, **kwargs):
        if not self.reference_id:
            last_quotation = Quotation.objects.all().order_by('id').last()
            last_id = int(last_quotation.reference_id.replace(self.REFERENCE_PREFIX, '')) if last_quotation and last_quotation.reference_id.startswith(self.REFERENCE_PREFIX) else 1000
            self.reference_id = f'{self.REFERENCE_PREFIX}{str(last_id + 1)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference_id

    # -------- Helpers for exports --------
    @property
    def date_str(self):
        """String version of date for CSV/XLSX export (avoids Excel ### date rendering)."""
        return self.date.strftime("%Y-%m-%d") if self.date else ""

    @property
    def lifts_str(self):
        """Comma-separated list of related lifts for safe CSV/XLSX export."""
        return ", ".join(str(lift) for lift in self.lifts.all())

    # Helper methods for export (return string values for ForeignKey fields)
    def customer_value(self):
        """Return customer site_name for export"""
        return self.customer.site_name if self.customer else ""
    customer_value.short_description = "Customer"

    def amc_type_value(self):
        """Return AMC type name for export"""
        return self.amc_type.name if self.amc_type else ""
    amc_type_value.short_description = "AMC Type"

    def sales_service_executive_value(self):
        """Return sales/service executive username for export"""
        return self.sales_service_executive.username if self.sales_service_executive else ""
    sales_service_executive_value.short_description = "Sales/Service Executive"
    

# quotation/views.py (ViewSet and Grouping)

from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

class QuotationViewSet(SnippetViewSet):
    model = Quotation
    icon = "doc-full"
    menu_label = "Quotations"
    inspect_view_enabled = True

    # ✅ Admin list columns
    list_display = (
        "reference_id",
        "customer",
        "amc_type",
        "sales_service_executive",
        "type",
        "year_of_make",
        "date",
    )

    # ✅ Export model fields (with stringified date/lifts for Excel)
    list_export = [
        "id",
        "reference_id",
        "customer_value",
        "amc_type_value",
        "sales_service_executive_value",
        "lifts_str",
        "type",
        "year_of_make",
        "date_str",
        "remark",
        "other_remark",
        "uploads_files",
    ]
    export_formats = ["csv", "xlsx"]

    # ✅ Search & filters
    search_fields = (
        "reference_id",
        "customer__site_name",
        "sales_service_executive__username",
        "type",
    )
    list_filter = ("type", "date")

    def get_add_url(self):
        return reverse("add_quotation_custom")

    def get_edit_url(self, instance):
        return reverse("edit_quotation_custom", args=(instance.reference_id,))

    def add_view(self, request):
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            # Check if this is an export request
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                # Only allow superusers to export
                if not request.user.is_superuser:
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export quotations.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)
    
    index_view_class = RestrictedIndexView


# ---------- Proxy model for Bulk Import ----------
class BulkImportQuotation(Quotation):
    """Proxy model used only for menu structure - redirects to bulk import view"""
    class Meta:
        proxy = True
        verbose_name = "Bulk Import"
        verbose_name_plural = "Bulk Import"


# Custom ViewSet for Bulk Import
class BulkImportQuotationViewSet(SnippetViewSet):
    """Custom ViewSet for Bulk Import Quotations"""
    model = BulkImportQuotation
    menu_label = "Bulk Import"
    icon = "download"
    menu_order = 200
    add_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    inspect_view_enabled = False
    
    # Override the index view to show bulk import page
    class BulkImportIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            # Redirect to bulk import view instead of showing list
            from django.shortcuts import render
            from Quotation import views
            return views.bulk_import_view(request)
    
    index_view_class = BulkImportIndexView


# ---------- SNIPPET GROUP ----------
class QuotationGroup(SnippetViewSetGroup):
    items = (
        QuotationViewSet,
        BulkImportQuotationViewSet,
    )
    menu_icon = "group"
    menu_label = "Quotation "
    menu_name = "quotation"


# ---------- REGISTER GROUP ----------
# QuotationGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# register_snippet(QuotationGroup)
