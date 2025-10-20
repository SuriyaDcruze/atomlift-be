from django.db import models
from django.urls import reverse
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
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

    # ✅ Export ALL model fields
    list_export = [
        "id",
        "reference_id",
        "customer",
        "amc_type",
        "sales_service_executive",
        "lifts",
        "type",
        "year_of_make",
        "date",
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

# ---------- SNIPPET GROUP ----------
class QuotationGroup(SnippetViewSetGroup):
    items = (QuotationViewSet,)
    menu_icon = "group"
    menu_label = "Quotation "
    menu_name = "quotation"


# ---------- REGISTER GROUP ----------
# QuotationGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# register_snippet(QuotationGroup)
