# invoice/models.py (Wagtail Integration)

from django.db import models
from datetime import date as py_date
from django.utils.dateparse import parse_date
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
    STATUS_CHOICES = [('open', 'Open'), ('paid', 'Paid'), ('partially_paid', 'Partially Paid'), ('due', 'Due')]
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

        # Coerce start_date/due_date if they were assigned as strings (common for JSON payloads)
        if isinstance(self.start_date, str):
            parsed = parse_date(self.start_date)
            if parsed:
                self.start_date = parsed
        if isinstance(self.due_date, str):
            parsed = parse_date(self.due_date)
            if parsed:
                self.due_date = parsed
        
        # Auto-update status to 'due' if due_date has passed and invoice is not paid
        from django.utils import timezone
        if self.due_date and self.status != 'paid':
            if isinstance(self.due_date, py_date) and self.due_date < timezone.now().date():
                self.status = 'due'
        
        super().save(*args, **kwargs)
        
        # Auto-send reminder emails (runs after save to ensure invoice exists)
        self._auto_send_reminder_if_needed()
    
    def _auto_send_reminder_if_needed(self):
        """
        Automatically send payment reminder emails when:
        - Invoice is overdue (due_date passed) and no reminder sent in last 7 days
        - Invoice is due today and no reminder sent today
        - Invoice is due in 3 days and no reminder sent for this cycle
        Only sends for unpaid invoices (open, partially_paid, due)
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Skip if invoice is paid or no customer email
        if self.status == 'paid':
            return
        if not self.customer or not self.customer.email:
            return
        if not self.due_date:
            return
        
        today = timezone.now().date()
        
        # Determine reminder type
        reminder_type = None
        days_diff = (self.due_date - today).days if isinstance(self.due_date, py_date) else 0
        
        # Use related name to check existing reminders (avoids circular import)
        if days_diff < 0:
            # Overdue - send if no reminder in last 7 days
            recent = self.reminders.filter(
                reminder_type='overdue',
                reminder_date__gte=timezone.now() - timedelta(days=7)
            ).exists()
            if not recent:
                reminder_type = 'overdue'
        elif days_diff == 0:
            # Due today - send if no reminder today
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            recent = self.reminders.filter(
                reminder_type='due_today',
                reminder_date__gte=today_start
            ).exists()
            if not recent:
                reminder_type = 'due_today'
        elif days_diff == 3:
            # Due in 3 days - send if no reminder in last 3 days
            recent = self.reminders.filter(
                reminder_type='due_soon',
                reminder_date__gte=timezone.now() - timedelta(days=3)
            ).exists()
            if not recent:
                reminder_type = 'due_soon'
        
        if reminder_type:
            self._send_reminder_email(reminder_type)
    
    def _send_reminder_email(self, reminder_type):
        """Send reminder email for this invoice"""
        from django.core.mail import EmailMessage
        from django.conf import settings
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            customer = self.customer
            if not customer or not customer.email:
                return False
            
            today = timezone.now().date()
            total_amount = self.get_total()
            
            # Build subject and urgency message
            if reminder_type == 'due_soon':
                days_until = (self.due_date - today).days if self.due_date else 0
                subject = f'Payment Reminder: Invoice {self.reference_id} is due in {days_until} day(s)'
                urgency = f"Your invoice is due in {days_until} day(s)."
            elif reminder_type == 'due_today':
                subject = f'Payment Reminder: Invoice {self.reference_id} is due TODAY'
                urgency = "Your invoice is due TODAY."
            else:
                days_overdue = (today - self.due_date).days if self.due_date else 0
                subject = f'URGENT: Invoice {self.reference_id} is {days_overdue} day(s) overdue'
                urgency = f"Your invoice is {days_overdue} day(s) OVERDUE."
            
            email_body = f"""Dear {customer.site_name or 'Valued Customer'},

This is a friendly reminder regarding your invoice.

Invoice Details:
- Invoice Number: {self.reference_id}
- Invoice Date: {self.start_date.strftime('%d/%m/%Y') if self.start_date else 'N/A'}
- Due Date: {self.due_date.strftime('%d/%m/%Y') if self.due_date else 'N/A'}
- Amount Due: ₹{total_amount:.2f}
- Current Status: {self.get_status_display()}

{urgency}

Please make payment at your earliest convenience to avoid any service interruptions.

Payment Methods:
- Cash
- Cheque
- NEFT

If you have already made the payment, please ignore this reminder.

Thank you for your business.

Best regards,
Atom Lifts India Pvt Ltd
Phone: 9600087456
Email: admin@atomlifts.com
"""
            
            email = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=settings.EMAIL_HOST_USER,
                to=[customer.email],
            )
            email.send()
            
            # Record reminder using related manager
            self.reminders.create(
                reminder_type=reminder_type,
                sent_to_email=customer.email,
                sent_successfully=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending auto reminder for invoice {self.reference_id}: {str(e)}")
            
            # Record failed reminder
            try:
                self.reminders.create(
                    reminder_type=reminder_type,
                    sent_to_email=customer.email if customer and customer.email else '',
                    sent_successfully=False,
                    error_message=str(e)
                )
            except:
                pass
            
            return False

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

    # -------- Helpers for exports --------
    @property
    def start_date_str(self):
        """String version of start_date for CSV/XLSX export (avoids Excel ### date rendering)."""
        return self.start_date.strftime("%Y-%m-%d") if self.start_date else ""

    @property
    def due_date_str(self):
        """String version of due_date for CSV/XLSX export."""
        return self.due_date.strftime("%Y-%m-%d") if self.due_date else ""

    # Helper methods for export (return string values for ForeignKey fields)
    def customer_value(self):
        """Return customer site_name for export"""
        return self.customer.site_name if self.customer else ""
    customer_value.short_description = "Customer"

    def amc_type_value(self):
        """Return AMC type name for export"""
        return self.amc_type.name if self.amc_type else ""
    amc_type_value.short_description = "AMC Type"


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

from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from django.http import HttpResponseForbidden

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
    
    # Export fields (use stringified dates so Excel doesn't render them as ###)
    list_export = [
        "reference_id",
        "customer_value",
        "amc_type_value",
        "start_date_str",
        "due_date_str",
        "discount",
        "payment_term",
        "total",
        "status",
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

    # Custom IndexView to restrict export to superusers and auto-update overdue invoices
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions and update overdue invoices"""
            # Auto-update overdue invoices before displaying the list
            from invoice.utils import update_overdue_invoices
            update_overdue_invoices()
            
            # Check if this is an export request
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                # Only allow superusers to export
                if not request.user.is_superuser:
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export invoices.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)
    
    index_view_class = RestrictedIndexView


# ---------- Proxy model for Bulk Import ----------
class BulkImportInvoice(Invoice):
    """Proxy model used only for menu structure - redirects to bulk import view"""
    class Meta:
        proxy = True
        verbose_name = "Bulk Import"
        verbose_name_plural = "Bulk Import"


# Custom ViewSet for Bulk Import
class BulkImportInvoiceViewSet(SnippetViewSet):
    """Custom ViewSet for Bulk Import Invoices"""
    model = BulkImportInvoice
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
            from invoice import views
            return views.bulk_import_view(request)
    
    index_view_class = BulkImportIndexView


# Invoice Reminder Tracking Model
class InvoiceReminder(models.Model):
    """Track invoice payment reminders sent to customers"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reminders')
    reminder_date = models.DateTimeField(auto_now_add=True)
    reminder_type = models.CharField(
        max_length=20,
        choices=[
            ('due_soon', 'Due Soon (3 days before)'),
            ('due_today', 'Due Today'),
            ('overdue', 'Overdue'),
        ],
        default='overdue'
    )
    sent_to_email = models.EmailField()
    sent_successfully = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Invoice Reminder"
        verbose_name_plural = "Invoice Reminders"
        ordering = ['-reminder_date']
    
    def __str__(self):
        return f"Reminder for {self.invoice.reference_id} - {self.reminder_date.strftime('%Y-%m-%d %H:%M')}"


# ---------- InvoiceReminder ViewSet ----------
class InvoiceReminderViewSet(SnippetViewSet):
    """ViewSet for viewing invoice reminders (read-only, auto-created)"""
    model = InvoiceReminder
    icon = "mail"
    menu_label = "Reminders"
    menu_order = 300
    list_display = ('invoice', 'reminder_type', 'sent_to_email', 'sent_successfully', 'reminder_date')
    list_filter = ('reminder_type', 'sent_successfully', 'reminder_date')
    search_fields = ('invoice__reference_id', 'sent_to_email')
    inspect_view_enabled = True
    create_view_enabled = False  # Hide the add button (same as Routine Services)
    edit_view_enabled = False
    delete_view_enabled = True
    list_display_add_buttons = None  # Hide the add button from list view header (same as Routine Services)
    
    # Hide add button completely - reminders are auto-generated only
    def get_add_url(self):
        return None
    
    def add_view(self, request):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Invoice reminders are automatically generated. Manual creation is not allowed.")
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add/edit permissions"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddInvoiceReminderPermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding/editing invoice reminders"""
            def user_has_permission(self, user, action):
                if action in ["add", "edit"]:
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddInvoiceReminderPermissionPolicy(self.model)


# ---------- SNIPPET GROUP ----------
class InvoiceGroup(SnippetViewSetGroup):
    # All invoice-related ViewSets grouped together
    items = (
        InvoiceViewSet,
        InvoiceReminderViewSet,
        BulkImportInvoiceViewSet,
    )
    menu_icon = "group"
    menu_label = "Invoices"
    menu_name = "invoicing"


# ---------- REGISTER GROUP ----------
# InvoiceGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# register_snippet(InvoiceGroup)