# invoice/models.py (Wagtail Integration)

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

# Assuming these models are imported or lazily referenced correctly
# from customer.models import Customer
# from authentication.models import Item (Required for InvoiceItem)


class Invoice(ClusterableModel):
    REFERENCE_PREFIX = 'INV'
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    
    # Using 'customer.Customer' for lazy reference
    customer = models.ForeignKey('customer.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    # amc_type (Commented out in your source, but often necessary)
    amc_type = models.ForeignKey('amc.AMCType', on_delete=models.PROTECT, null=False, blank=False)
    
    start_date = models.DateField()
    due_date = models.DateField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    PAYMENT_CHOICES = [('cash', 'Cash'), ('cheque', 'Cheque'), ('neft', 'NEFT')]
    payment_term = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    uploads_files = models.FileField(upload_to='invoice_uploads/', null=True, blank=True, max_length=100)
    STATUS_CHOICES = [('open', 'Open'), ('paid', 'Paid'), ('partially_paid', 'Partially Paid')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    panels = [
        MultiFieldPanel([
            FieldPanel('reference_id', read_only=True),
            FieldPanel('customer'),
            FieldPanel('amc_type'), # Uncomment if AMCType is used
            FieldPanel('start_date'),
            FieldPanel('due_date'),
            FieldPanel('discount'),
            FieldPanel('payment_term'),
            FieldPanel('status'),
            FieldPanel('uploads_files'),
        ], heading="Invoice Details"),
        InlinePanel('items', label="Invoice Items"),
    ]

    def save(self, *args, **kwargs):
        if not self.reference_id:
            last_invoice = Invoice.objects.all().order_by('id').last()
            # Safely generate reference_id
            last_id = int(last_invoice.reference_id.replace(self.REFERENCE_PREFIX, '')) if last_invoice and last_invoice.reference_id.startswith(self.REFERENCE_PREFIX) else 0
            self.reference_id = f'{self.REFERENCE_PREFIX}{str(last_id + 1).zfill(3)}'
        super().save(*args, **kwargs)
    
    def get_subtotal(self):
        """Calculate subtotal amount from all invoice items (before discount)"""
        return round(sum(item.total for item in self.items.all()), 2)
    
    def get_discount_amount(self):
        """Calculate discount amount"""
        subtotal = self.get_subtotal()
        return round(subtotal * (self.discount / 100), 2)
    
    def get_total(self):
        """Calculate total amount from all invoice items"""
        subtotal = self.get_subtotal()
        discount_amount = self.get_discount_amount()
        return round(subtotal - discount_amount, 2)
    
    @property
    def invoice_no(self):
        """Alias for reference_id for template compatibility"""
        return self.reference_id
    
    @property
    def invoice_date(self):
        """Alias for start_date for template compatibility"""
        return self.start_date
    
    @property
    def total(self):
        """Calculate and return total amount"""
        return self.get_total()

    def __str__(self):
        return self.reference_id


class InvoiceItem(models.Model):
    # Relates back to the parent Invoice
    invoice = ParentalKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('items.Item', on_delete=models.SET_NULL, null=True, blank=True)
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
        # Calculation from original logic
        self.total = self.rate * self.qty * (1 + (self.tax / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item for {self.invoice.reference_id}"
    

# invoice/models.py (ViewSet and Grouping)

from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

class InvoiceViewSet(SnippetViewSet):
    model = Invoice
    icon = "folder-open-inverse"
    menu_label = "Invoices"
    inspect_view_enabled = True
   
    list_display = ('reference_id', 'customer', 'start_date', 'due_date', 'total', 'status')
    
    # Search fields
    search_fields = (
        'reference_id',
        'customer__site_name',
        'customer__site_id',
        'customer__job_no',
        'customer__email',
        'customer__phone',
        'customer__mobile',
        'status',
        'note',
    )
    
    # Filter fields
    list_filter = (
        'status',
        'customer',
        'start_date',
        'due_date',
    )
    
    # You can customize export fields here if needed
    list_export = [
        "reference_id", "customer", "start_date", "due_date",
        "discount", "payment_term", "total", "status",
    ]

    def get_add_url(self):
        from django.urls import reverse
        return reverse("add_invoice_custom")

    def get_view_url(self, instance):
        from django.urls import reverse
        return reverse("view_invoice_custom", args=(instance.reference_id,))

    def get_edit_url(self, instance):
        from django.urls import reverse
        return reverse("edit_invoice_custom", args=(instance.reference_id,))

    def add_view(self, request):
        from django.shortcuts import redirect
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        from django.shortcuts import redirect
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))


# ---------- SNIPPET GROUP ----------
class InvoiceGroup(SnippetViewSetGroup):
    # Only one ViewSet for this group
    items = (InvoiceViewSet,) 
    menu_icon = "group"
    menu_label = "Invoices"
    menu_name = "invoicing"


# ---------- REGISTER GROUP ----------
# InvoiceGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# register_snippet(InvoiceGroup)