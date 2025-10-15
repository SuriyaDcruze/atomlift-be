# recurring_invoice/models.py (Wagtail Integration)

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from datetime import timedelta


class RecurringInvoice(ClusterableModel):
    REFERENCE_PREFIX = 'RINV'
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    customer = models.ForeignKey(
        'customer.Customer',  # Using lazy string reference
        on_delete=models.SET_NULL, null=True, blank=True
    )
    profile_name = models.CharField(max_length=100)
    order_number = models.CharField(max_length=50, blank=True)

    REPEAT_CHOICES = [
        ('week', 'Week'), ('2week', '2 Weeks'), ('month', 'Month'), ('2month', '2 Months'),
        ('3month', '3 Months'), ('6month', '6 Months'), ('year', 'Year'), ('2year', '2 Years'),
    ]
    repeat_every = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='month')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    last_generated_date = models.DateField(null=True, blank=True)

    # sales_person = models.ForeignKey(
    #     'authentication.CustomUser',  # CORRECTED: Using lazy string reference
    #     on_delete=models.SET_NULL, null=True, blank=True,
    #     limit_choices_to={"role": "SALESMAN"}
    # )

    billing_address = models.TextField(blank=True)
    gst_treatment = models.CharField(max_length=50, blank=True)
    uploads_files = models.FileField(upload_to='recurring_invoice_uploads/', null=True, blank=True, max_length=100)

    STATUS_CHOICES = [('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    panels = [
        MultiFieldPanel([
            FieldPanel('customer'),
            FieldPanel('profile_name'),
            FieldPanel('order_number'),
            FieldPanel('repeat_every'),
            FieldPanel('start_date'),
            FieldPanel('end_date'),
            #FieldPanel('sales_person'),  # UNCOMMENTED
            FieldPanel('billing_address'),
            FieldPanel('gst_treatment'),
            FieldPanel('uploads_files'),
            FieldPanel('status'),
            FieldPanel('last_generated_date', read_only=True),
        ], heading="Recurring Details"),
        InlinePanel('items', label="Recurring Invoice Items"),
    ]

    def save(self, *args, **kwargs):
        if not self.reference_id:
            last_invoice = RecurringInvoice.objects.all().order_by('id').last()
            last_id = int(last_invoice.reference_id.replace(self.REFERENCE_PREFIX, '')) if last_invoice and last_invoice.reference_id.startswith(self.REFERENCE_PREFIX) else 0
            self.reference_id = f'{self.REFERENCE_PREFIX}{str(last_id + 1).zfill(3)}'
        if self.customer and not self.billing_address:
            # Assuming the 'customer' object is loaded when accessed
            self.billing_address = self.customer.site_address
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference_id
    
    def get_next_date(self):
        if not self.last_generated_date: return self.start_date
        mapping = {'week': 7, '2week': 14, 'month': 30, '2month': 60, '3month': 90, '6month': 180, 'year': 365, '2year': 730}
        return self.last_generated_date + timedelta(days=mapping.get(self.repeat_every, 30))


class RecurringInvoiceItem(models.Model):
    recurring_invoice = ParentalKey(RecurringInvoice, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(
        'items.Item',  # Using lazy string reference based on your code
        on_delete=models.SET_NULL, null=True, blank=True
    )
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.IntegerField(default=1)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    panels = [
        FieldPanel('item'),
        FieldPanel('rate'),
        FieldPanel('qty'),
        FieldPanel('tax'),
        FieldPanel('total', read_only=True),
    ]

    def save(self, *args, **kwargs):
        self.total = self.rate * self.qty * (1 + (self.tax / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item for {self.recurring_invoice.reference_id}"
    

# recurring_invoice/models.py (ViewSet and Grouping)

from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

class RecurringInvoiceViewSet(SnippetViewSet):
    model = RecurringInvoice
    icon = "repeat"
    menu_label = "Recurring Invoices"
    inspect_view_enabled = True
    list_display = ('reference_id', 'customer', 'profile_name', 'repeat_every', 'start_date', 'status')
    search_fields = ('reference_id', 'customer__site_name', 'profile_name', 'status')


# ---------- SNIPPET GROUP ----------
class RecurringInvoiceGroup(SnippetViewSetGroup):
    # Only one ViewSet for this group
    items = (RecurringInvoiceViewSet,) 
    icon = "calculator"
    menu_label = "Recurring Billing"
    menu_name = "recurring_billing_management"


# ---------- REGISTER GROUP ----------
register_snippet(RecurringInvoiceGroup)