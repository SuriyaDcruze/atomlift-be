# recurring_invoice/models.py (Wagtail Integration)

from django.db import models
from django.urls import reverse, path
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from authentication.models import CustomUser  # Corrected import
import re


class RecurringInvoice(ClusterableModel):
    REFERENCE_PREFIX = 'RINV'
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    customer = models.ForeignKey(
        'customer.Customer',  # Using lazy string reference
        on_delete=models.SET_NULL, null=True, blank=True
    )
    profile_name = models.CharField(max_length=100)
    order_number = models.CharField(max_length=50, blank=True)
    
    def clean(self):
        super().clean()
        if self.profile_name:
            # Check for special characters (allow only letters, numbers, spaces, hyphens, and underscores)
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', self.profile_name):
                raise ValidationError({
                    'profile_name': _('Profile name cannot contain special characters. Only letters, numbers, spaces, hyphens, and underscores are allowed.')
                })
        if self.gst_treatment:
            # Check for special characters (allow only letters, numbers, spaces, hyphens, and underscores)
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', self.gst_treatment):
                raise ValidationError({
                    'gst_treatment': _('GST Treatment cannot contain special characters. Only letters, numbers, spaces, hyphens, and underscores are allowed.')
                })

    REPEAT_CHOICES = [
        ('week', 'Week'), ('2week', '2 Weeks'), ('month', 'Month'), ('2month', '2 Months'),
        ('3month', '3 Months'), ('6month', '6 Months'), ('year', 'Year'), ('2year', '2 Years'),
    ]
    repeat_every = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='month')
    auto_repeat = models.BooleanField(default=True, help_text="Enable automatic invoice generation based on repeat_every schedule")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    last_generated_date = models.DateField(null=True, blank=True)

    sales_person = models.ForeignKey(
    CustomUser,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    limit_choices_to={'groups__name': 'employee'},  # ✅ FIXED
    related_name='assigned_recurring_invoices',)

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
            FieldPanel('auto_repeat'),
            FieldPanel('start_date'),
            FieldPanel('end_date'),
            FieldPanel('sales_person'),  # UNCOMMENTED
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
        """
        Calculate the next invoice generation date based on repeat_every schedule
        Uses proper date calculations for months/years (relativedelta) to handle edge cases
        """
        from django.utils import timezone
        
        # Base date: use last_generated_date if exists, otherwise use start_date
        base_date = self.last_generated_date if self.last_generated_date else self.start_date
        
        # Calculate next date based on repeat_every using proper date arithmetic
        if self.repeat_every == 'week':
            next_date = base_date + timedelta(days=7)
        elif self.repeat_every == '2week':
            next_date = base_date + timedelta(days=14)
        elif self.repeat_every == 'month':
            next_date = base_date + relativedelta(months=1)
        elif self.repeat_every == '2month':
            next_date = base_date + relativedelta(months=2)
        elif self.repeat_every == '3month':
            next_date = base_date + relativedelta(months=3)
        elif self.repeat_every == '6month':
            next_date = base_date + relativedelta(months=6)
        elif self.repeat_every == 'year':
            next_date = base_date + relativedelta(years=1)
        elif self.repeat_every == '2year':
            next_date = base_date + relativedelta(years=2)
        else:
            # Default fallback: 30 days
            next_date = base_date + timedelta(days=30)
        
        # Check if next_date exceeds end_date (if set)
        if self.end_date and next_date > self.end_date:
            return None  # No more invoices to generate
        
        # Check if next_date is in the past (shouldn't happen for active invoices)
        today = timezone.now().date()
        if next_date < today and self.status == 'active':
            # If next date is in the past, recalculate from today
            return self._calculate_next_from_date(today)
        
        return next_date
    
    def _calculate_next_from_date(self, from_date):
        """Helper method to calculate next date from a given date"""
        if self.repeat_every == 'week':
            return from_date + timedelta(days=7)
        elif self.repeat_every == '2week':
            return from_date + timedelta(days=14)
        elif self.repeat_every == 'month':
            return from_date + relativedelta(months=1)
        elif self.repeat_every == '2month':
            return from_date + relativedelta(months=2)
        elif self.repeat_every == '3month':
            return from_date + relativedelta(months=3)
        elif self.repeat_every == '6month':
            return from_date + relativedelta(months=6)
        elif self.repeat_every == 'year':
            return from_date + relativedelta(years=1)
        elif self.repeat_every == '2year':
            return from_date + relativedelta(years=2)
        else:
            return from_date + timedelta(days=30)
    
    @property
    def next_invoice_date(self):
        """
        Property to get the next invoice generation date
        Returns None if no more invoices should be generated
        """
        from django.utils import timezone
        
        if not self.auto_repeat or self.status != 'active':
            return None
        
        next_date = self.get_next_date()
        
        # Check if we've passed the end date
        if self.end_date:
            today = timezone.now().date()
            if today > self.end_date:
                return None
        
        return next_date
    
    def is_renewal_needed(self, days_before_expiry=30):
        """
        Check if recurring invoice needs renewal based on end date proximity
        Args:
            days_before_expiry: Number of days before end date to show renewal option
        Returns:
            bool: True if renewal is needed, False otherwise
        """
        if not self.end_date or self.status != 'active':
            return False
        
        from django.utils import timezone
        today = timezone.now().date()
        days_until_expiry = (self.end_date - today).days
        
        # Show renewal button if:
        # 1. End date has passed (days_until_expiry < 0)
        # 2. End date is within the specified days (days_until_expiry <= days_before_expiry)
        return days_until_expiry <= days_before_expiry
    
    def can_renew(self):
        """
        Check if recurring invoice can be renewed
        Returns:
            bool: True if can be renewed, False otherwise
        """
        # Allow renewal if:
        # 1. Status is active
        # 2. Has an end date (not indefinite)
        # 3. End date has passed or is close to passing
        return self.status == 'active' and self.end_date is not None
    
    def renew_recurring_invoice(self, new_end_date=None, extend_days=None):
        """
        Renew the recurring invoice by extending the end date
        Args:
            new_end_date: Specific new end date (optional)
            extend_days: Number of days to extend from current end date (optional)
        Returns:
            bool: True if renewal successful, False otherwise
        """
        if not self.can_renew():
            return False
        
        try:
            if new_end_date:
                self.end_date = new_end_date
            elif extend_days:
                self.end_date = self.end_date + timedelta(days=extend_days)
            else:
                # Default: extend by the same period as repeat_every using proper date calculations
                if self.repeat_every == 'week':
                    self.end_date = self.end_date + timedelta(days=7)
                elif self.repeat_every == '2week':
                    self.end_date = self.end_date + timedelta(days=14)
                elif self.repeat_every == 'month':
                    self.end_date = self.end_date + relativedelta(months=1)
                elif self.repeat_every == '2month':
                    self.end_date = self.end_date + relativedelta(months=2)
                elif self.repeat_every == '3month':
                    self.end_date = self.end_date + relativedelta(months=3)
                elif self.repeat_every == '6month':
                    self.end_date = self.end_date + relativedelta(months=6)
                elif self.repeat_every == 'year':
                    self.end_date = self.end_date + relativedelta(years=1)
                elif self.repeat_every == '2year':
                    self.end_date = self.end_date + relativedelta(years=2)
                else:
                    self.end_date = self.end_date + timedelta(days=30)
            
            self.save()
            return True
        except Exception as e:
            print(f"Error renewing recurring invoice {self.reference_id}: {e}")
            return False
    
    def get_renewal_info(self):
        """
        Get renewal information for display
        Returns:
            dict: Renewal information including days until expiry, renewal options, etc.
        """
        if not self.end_date:
            return {'needs_renewal': False, 'message': 'No end date set - indefinite recurring'}
        
        from django.utils import timezone
        today = timezone.now().date()
        days_until_expiry = (self.end_date - today).days
        
        # Calculate default extension days based on repeat_every
        if self.repeat_every == 'week':
            default_extension = 7
        elif self.repeat_every == '2week':
            default_extension = 14
        elif self.repeat_every == 'month':
            default_extension = 30  # Approximate
        elif self.repeat_every == '2month':
            default_extension = 60  # Approximate
        elif self.repeat_every == '3month':
            default_extension = 90  # Approximate
        elif self.repeat_every == '6month':
            default_extension = 180  # Approximate
        elif self.repeat_every == 'year':
            default_extension = 365  # Approximate
        elif self.repeat_every == '2year':
            default_extension = 730  # Approximate
        else:
            default_extension = 30
        
        return {
            'needs_renewal': self.is_renewal_needed(),
            'days_until_expiry': days_until_expiry,
            'end_date': self.end_date,
            'can_renew': self.can_renew(),
            'default_extension_days': default_extension,
            'status': self.status
        }


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
        from decimal import Decimal
        # Ensure values are Decimal for accurate calculation
        rate = Decimal(str(self.rate)) if self.rate else Decimal('0')
        qty = Decimal(str(self.qty)) if self.qty else Decimal('1')
        tax = Decimal(str(self.tax)) if self.tax else Decimal('0')
        
        self.total = rate * qty * (1 + (tax / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        try:
            # Handle item name safely
            if self.item:
                if hasattr(self.item, 'name'):
                    item_name = str(self.item.name)
                elif isinstance(self.item, dict):
                    item_name = self.item.get('name', 'Unknown Item')
                else:
                    item_name = "Item"
            else:
                item_name = "No Item"
            
            # Handle invoice reference safely
            if self.recurring_invoice:
                if hasattr(self.recurring_invoice, 'reference_id'):
                    invoice_ref = str(self.recurring_invoice.reference_id)
                else:
                    invoice_ref = "Invoice"
            else:
                invoice_ref = "Unknown Invoice"
            
            return f"{item_name} for {invoice_ref}"
        except Exception as e:
            # Last resort fallback
            return f"RecurringInvoiceItem #{self.id if hasattr(self, 'id') and self.id else 'New'}"
    

# recurring_invoice/models.py (ViewSet and Grouping)

from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from django.http import HttpResponseForbidden

class RecurringInvoiceViewSet(SnippetViewSet):
    model = RecurringInvoice
    icon = "group"
    menu_label = "Recurring Invoices"
    inspect_view_enabled = True
    inspect_template_name = 'recurringInvoice/inspect_recurring_invoice.html'

    # ✅ Admin list view columns
    list_display = (
        "reference_id",
        "customer",
        "profile_name",
        "repeat_every",
        "start_date",
        "end_date",
        "last_generated_date",
        "status",
    )

    # ✅ Full export fields
    list_export = [
        "id",
        "reference_id",
        "customer",
        "profile_name",
        "order_number",
        "repeat_every",
        "auto_repeat",
        "start_date",
        "end_date",
        "last_generated_date",
        "sales_person",
        "billing_address",
        "gst_treatment",
        "uploads_files",
        "status",
    ]
    export_formats = ["csv", "xlsx"]

    # ✅ Filters & search
    list_filter = ("status", "repeat_every", "start_date")
    search_fields = (
        "reference_id",
        "customer__site_name",
        "profile_name",
        "sales_person__username",
        "status",
    )

    def get_add_url(self):
        return reverse("add_recurring_invoice_custom")

    def get_edit_url(self, instance):
        return reverse("edit_recurring_invoice_custom", args=(instance.reference_id,))

    def add_view(self, request):
        print("DEBUG: RecurringInvoiceViewSet.add_view called")
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        print(f"DEBUG: RecurringInvoiceViewSet.edit_view called with pk={pk}")
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                if not request.user.is_superuser:
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export recurring invoices.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)

    index_view_class = RestrictedIndexView

    def next_invoice_date_display(self, obj):
        """Display next invoice date in list view"""
        if not obj.auto_repeat:
            return "Auto-repeat disabled"
        if obj.status != 'active':
            return f"({obj.get_status_display})"
        
        next_date = obj.next_invoice_date
        if next_date:
            return next_date.strftime("%b. %d, %Y")
        else:
            return "N/A"
    
    next_invoice_date_display.short_description = "Next Invoice Date"
    next_invoice_date_display.admin_order_field = "last_generated_date"
    
    def last_generated_date_formatted(self, obj):
        """Display last generated date with custom formatting"""
        if obj.last_generated_date:
            return obj.last_generated_date.strftime("%b. %d, %Y")
        else:
            return "Not generated yet"
    
    last_generated_date_formatted.short_description = "Last Generated Date"
    last_generated_date_formatted.admin_order_field = "last_generated_date"
    
    def get_list_display(self, request):
        """Add custom display methods to list display"""
        display = list(super().get_list_display(request))
        # Replace last_generated_date with formatted version
        if 'last_generated_date' in display:
            display[display.index('last_generated_date')] = 'last_generated_date_formatted'
        # Insert next_invoice_date_display before status
        if 'status' in display:
            status_index = display.index('status')
            display.insert(status_index, 'next_invoice_date_display')
        else:
            display.append('next_invoice_date_display')
        display.append('renewal_status')
        return display
    
    def renewal_status(self, obj):
        """Show renewal status in list view"""
        if not obj.end_date:
            return "No end date"
        
        renewal_info = obj.get_renewal_info()
        days = renewal_info['days_until_expiry']
        
        if days < 0:
            return f"🚨 EXPIRED ({abs(days)} days ago)"
        elif days <= 7:
            return f"⚠️ Expires in {days} days"
        elif days <= 30:
            return f"🟡 Expires in {days} days"
        else:
            return f"✅ Active ({days} days)"
    
    renewal_status.short_description = "Renewal Status"
    
    def get_urlpatterns(self):
        """Add renewal URL pattern"""
        patterns = super().get_urlpatterns()
        patterns.append(
            path('renew/<int:pk>/', self.renew_view, name='renew')
        )
        return patterns
    
    def renew_view(self, request, pk):
        """Handle renewal of recurring invoice"""
        from django.shortcuts import render, get_object_or_404, redirect
        from django.contrib import messages
        from django.http import JsonResponse
        
        if request.method == 'POST':
            try:
                instance = get_object_or_404(self.model, pk=pk)
                
                # Get renewal parameters
                renewal_option = request.POST.get('renewal_option', 'default')
                extend_days = request.POST.get('extend_days')
                new_end_date = request.POST.get('new_end_date')
                
                # Process renewal based on option
                if renewal_option == 'custom' and extend_days:
                    extend_days = int(extend_days)
                    new_end_date = None
                elif renewal_option == 'date' and new_end_date:
                    extend_days = None
                else:
                    # Default option - extend by same period
                    extend_days = None
                    new_end_date = None
                
                # Perform renewal
                old_end_date = instance.end_date
                success = instance.renew_recurring_invoice(
                    new_end_date=new_end_date,
                    extend_days=extend_days
                )
                
                if success:
                    messages.success(request, f'Recurring invoice {instance.reference_id} renewed successfully! New end date: {instance.end_date}')
                    return redirect('/admin/snippets/recurringInvoice/recurringinvoice/')
                else:
                    messages.error(request, 'Failed to renew recurring invoice.')
                    
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        
        # GET request - show renewal form
        instance = get_object_or_404(self.model, pk=pk)
        renewal_info = instance.get_renewal_info()
        
        context = {
            'instance': instance,
            'renewal_info': renewal_info,
            'title': f'Renew {instance.reference_id}',
        }
        
        return render(request, 'recurringInvoice/renew_modal.html', context)



# ---------- SNIPPET GROUP ----------
class RecurringInvoiceGroup(SnippetViewSetGroup):
    # Only one ViewSet for this group
    items = (RecurringInvoiceViewSet,) 
    menu_icon = "group"
    menu_label = "Recurring Invoices"
    menu_name = "recurring_billing"


# ---------- REGISTER GROUP ----------
# RecurringInvoiceGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# register_snippet(RecurringInvoiceGroup)
