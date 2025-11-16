from django.db import models
from django.utils import timezone
from datetime import timedelta
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from django.http import HttpResponseForbidden
import re

from customer.models import Customer
from items.models import Item


# ---------- Dropdown Snippets ----------
class AMCType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name


class PaymentTerms(models.Model):
    name = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name


# ---------- Main AMC ----------
class AMC(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    # amcname field removed - migration 0006_remove_amcname_field.py
    latitude = models.CharField(max_length=255, blank=True, null=True)      # site address
    equipment_no = models.CharField(max_length=50, blank=True, null=True)   # job no
    geo_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Latitude coordinate (-90 to 90). Auto-filled from customer."
    )
    geo_longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Longitude coordinate (-180 to 180). Auto-filled from customer."
    )
    invoice_frequency = models.CharField(
        max_length=20,
        choices=[
            ("annually", "Annually"),
            ("semi_annually", "Semi Annually"),
            ("quarterly", "Quarterly"),
            ("monthly", "Monthly"),
            ("per_service", "Per Service"),
        ],
        default="annually",
    )
    amc_type = models.ForeignKey(AMCType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="AMC Pack Type")
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_generate_contract = models.BooleanField(default=False, verbose_name="Generate Contract Now")
    no_of_services = models.IntegerField(default=12, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    no_of_lifts = models.IntegerField(default=0, blank=True, null=True)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    contract_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    total_amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    amc_service_item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
            ("on_hold", "On Hold"),
        ],
        default="active",
    )
    created = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate that amcname does not contain special characters"""
        super().clean()
        
        # Commented out - amcname field is no longer used
        # if self.amcname:
        #     # Allow letters, numbers, spaces, and hyphens
        #     if not re.match(r'^[a-zA-Z0-9\s\-]+$', self.amcname):
        #         raise ValidationError({
        #             'amcname': 'AMC Pack Name must not contain special characters. Only letters, numbers, spaces, and hyphens are allowed.'
        #         })

    def save(self, *args, **kwargs):
        """Call clean before saving"""
        self.full_clean()
        # Ensure date fields are date objects
        if isinstance(self.start_date, str):
            self.start_date = date.fromisoformat(self.start_date)
        if isinstance(self.end_date, str):
            self.end_date = date.fromisoformat(self.end_date)

        # Auto reference id
        if not self.reference_id:
            last_amc = AMC.objects.order_by("id").last()
            last_id = 0
            if last_amc and last_amc.reference_id.startswith("AMC"):
                try:
                    last_id = int(last_amc.reference_id.replace("AMC", ""))
                except ValueError:
                    pass
            self.reference_id = f"AMC{str(last_id + 1).zfill(2)}"

        # Default end_date = +1 year
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + timedelta(days=365)

        # Totals
        price = Decimal(str(self.price or 0))
        lifts = Decimal(str(self.no_of_lifts or 0))
        gst = Decimal(str(self.gst_percentage or 0))
        total_paid = Decimal(str(self.total_amount_paid or 0))

        if self.is_generate_contract:
            self.total = price * lifts * (Decimal("1") + gst / Decimal("100"))
        else:
            self.total = Decimal("0.00")

        self.contract_amount = self.total
        self.amount_due = self.contract_amount - total_paid

        today = timezone.now().date()
        if self.end_date and today > self.end_date:
            self.status = "expired"
        elif self.start_date > today:
            self.status = "on_hold"
        else:
            self.status = "active"

        super().save(*args, **kwargs)

    def get_current_status(self):
        """Calculate current status based on dates (dynamic calculation)"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # If manually cancelled, respect that
        if self.status == 'cancelled':
            return 'cancelled'
        
        # Check if expired
        if self.end_date and today > self.end_date:
            return 'expired'
        
        # Check if not started yet (on hold)
        if self.start_date and today < self.start_date:
            return 'on_hold'
        
        # Otherwise active
        return 'active'
    
    def get_status_display_name(self):
        """Get display name for current status"""
        status = self.get_current_status()
        status_map = {
            'active': 'Active',
            'expired': 'Expired',
            'cancelled': 'Cancelled',
            'on_hold': 'On Hold',
        }
        return status_map.get(status, status.title())
    
    @property
    def current_status(self):
        """Property to get current status for display in admin"""
        return self.get_status_display_name()
    
    @property
    def contract_period(self):
        """Property to display contract period as 'start_date - end_date'"""
        if self.start_date and self.end_date:
            return f"{self.start_date} - {self.end_date}"
        elif self.start_date:
            return f"{self.start_date} - (No end date)"
        return "Not set"
    
    def amount_details(self):
        """Method to display all amount details in a single column"""
        from django.utils.html import format_html
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong>Total Amount:</strong> ₹{}<br>'
            '<strong>Total Amount Paid:</strong> ₹{}<br>'
            '<strong>Due Amount:</strong> ₹{}'
            '</div>',
            self.contract_amount,
            self.total_amount_paid,
            self.amount_due
        )
    amount_details.short_description = 'Amount'
    
    def get_amc_type_display(self):
        """Method to display AMC Pack Type with proper formatting"""
        if self.amc_type:
            return str(self.amc_type)
        return "—"
    get_amc_type_display.short_description = 'AMC Pack Type'

    def __str__(self):
        return self.reference_id

    # -------- Helpers for exports --------
    @property
    def start_date_str(self):
        """String version of start_date for CSV/XLSX export (avoids Excel ### date rendering)."""
        return self.start_date.strftime("%Y-%m-%d") if self.start_date else ""

    @property
    def end_date_str(self):
        """String version of end_date for CSV/XLSX export."""
        return self.end_date.strftime("%Y-%m-%d") if self.end_date else ""

    @property
    def created_str(self):
        """String version of created datetime for CSV/XLSX export."""
        return self.created.strftime("%Y-%m-%d %H:%M") if self.created else ""

    # Wagtail panels
    basic_panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            FieldPanel("customer"),
            # FieldPanel("amcname"),  # Commented out - not needed
            FieldPanel("invoice_frequency"),
            FieldPanel("amc_type"),
            FieldPanel("payment_terms"),
        ], heading="Basic Details"),
        MultiFieldPanel([
            FieldPanel("start_date"),
            FieldPanel("end_date"),
            FieldPanel("equipment_no"),
            FieldPanel("latitude"),
            FieldPanel("notes"),
        ], heading="Schedule & Location"),
    ]

    contract_panels = [
        FieldPanel("is_generate_contract"),
        MultiFieldPanel([
            FieldPanel("amc_service_item"),
            FieldPanel("price"),
            FieldPanel("no_of_lifts"),
            FieldPanel("gst_percentage"),
            FieldPanel("no_of_services"),
        ], heading="Pricing"),
        FieldPanel("total_amount_paid"),
        MultiFieldPanel([
            FieldPanel("total", read_only=True),
            FieldPanel("contract_amount", read_only=True),
            FieldPanel("amount_due", read_only=True),
            FieldPanel("status", read_only=True),
            FieldPanel("created", read_only=True),
        ], heading="Totals & Status"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(basic_panels, heading="AMC Details"),
        ObjectList(contract_panels, heading="Contract & Pricing"),
    ])


# ---------- Wagtail admin viewsets ----------
class AMCTypeViewSet(SnippetViewSet):
    model = AMCType
    icon = "tag"
    menu_label = "AMC Pack Types"
    list_display = ("name",)


class PaymentTermsViewSet(SnippetViewSet):
    model = PaymentTerms
    icon = "form"
    menu_label = "Payment Terms"
    list_display = ("name",)


class AMCViewSet(SnippetViewSet):
    model = AMC
    icon = "calendar"
    menu_label = "All AMCs"
    inspect_view_enabled = True
    create_template_name = 'amc/add_amc_custom.html'
    inspect_view_fields = [
        'reference_id',
        'customer',
        'amc_type',  # AMC Pack Type
        'invoice_frequency',
        'start_date',
        'end_date',
        'equipment_no',
        'latitude',
        'notes',
        'is_generate_contract',
        'no_of_services',
        'price',
        'no_of_lifts',
        'gst_percentage',
        'total',
        'contract_amount',
        'total_amount_paid',
        'amount_due',
        'amc_service_item',
        'status',
        'created',
    ]

    # 👇 Columns shown in admin list
    list_display = (
        "reference_id",
        "customer",
        "get_amc_type_display",
        # "amcname",  # Commented out - not needed
        "current_status",
        "contract_period",
        "amount_details",
    )

    # 👇 Export ALL model fields to CSV & XLSX (dates as strings for Excel)
    list_export = [
        "id",
        "reference_id",
        "customer",
        # "amcname",  # Commented out - not needed
        "latitude",
        "equipment_no",
        "invoice_frequency",
        "amc_type",
        "payment_terms",
        "start_date_str",
        "end_date_str",
        "notes",
        "is_generate_contract",
        "no_of_services",
        "price",
        "no_of_lifts",
        "gst_percentage",
        "total",
        "contract_amount",
        "total_amount_paid",
        "amount_due",
        "amc_service_item",
        "status",
        "created_str",
    ]
    export_formats = ["csv", "xlsx"]

    # 👇 Searchable fields
    search_fields = (
        "reference_id",
        # "amcname",  # Commented out - not needed
        "customer__site_name",
        "equipment_no",
    )

    # 👇 Filter fields
    list_filter = (
        "status",
        "customer",
        "amc_type",
        "invoice_frequency",
        "start_date",
        "end_date",
        "is_generate_contract",
        "created",
    )

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
                    messages.error(request, "You do not have permission to export AMCs.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)
    
    index_view_class = RestrictedIndexView

    def get_add_url(self):
        from django.urls import reverse
        return reverse("add_amc_custom")

    def get_edit_url(self, instance):
        from django.urls import reverse
        return reverse("edit_amc_custom", args=(instance.pk,))

    def add_view(self, request):
        from django.shortcuts import redirect
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        from django.shortcuts import redirect
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))


class AMCExpiringThisMonth(AMC):
    class Meta:
        proxy = True
        verbose_name = "This Month Expiring AMC"
        verbose_name_plural = "This Month Expiring AMCs"


class AMCExpiringLastMonth(AMC):
    class Meta:
        proxy = True
        verbose_name = "Last Month Expired AMC"
        verbose_name_plural = "Last Month Expired AMCs"


class AMCExpiringNextMonth(AMC):
    class Meta:
        proxy = True
        verbose_name = "Next Month Expiring AMC"
        verbose_name_plural = "Next Month Expiring AMCs"


class AMCExpiringThisMonthViewSet(SnippetViewSet):
    model = AMCExpiringThisMonth
    icon = "date"
    menu_label = "This Month Expiring"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None  # Hide the add button from list view header

    list_display = (
        "reference_id",
        "customer",
        "get_amc_type_display",
        # "amcname",  # Commented out - not needed
        "current_status",
        "contract_period",
        "amount_details",
    )

    list_export = [
        "id",
        "reference_id",
        "customer",
        # "amcname",  # Commented out - not needed
        "latitude",
        "equipment_no",
        "invoice_frequency",
        "amc_type",
        "payment_terms",
        "start_date_str",
        "end_date_str",
        "notes",
        "is_generate_contract",
        "no_of_services",
        "price",
        "no_of_lifts",
        "gst_percentage",
        "total",
        "contract_amount",
        "total_amount_paid",
        "amount_due",
        "amc_service_item",
        "status",
        "created_str",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "reference_id",
        # "amcname",  # Commented out - not needed
        "customer__site_name",
        "equipment_no",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        first_day = today.replace(day=1)
        if first_day.month == 12:
            next_month_first = first_day.replace(year=first_day.year + 1, month=1, day=1)
        else:
            next_month_first = first_day.replace(month=first_day.month + 1, day=1)
        last_day = next_month_first - timedelta(days=1)
        return AMC.objects.filter(end_date__gte=first_day, end_date__lte=last_day).order_by("end_date")
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add/edit/delete permissions"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddAMCExpiringPermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding/editing/deleting AMC expiring records"""
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddAMCExpiringPermissionPolicy(self.model)


class AMCExpiringLastMonthViewSet(SnippetViewSet):
    model = AMCExpiringLastMonth
    icon = "date"
    menu_label = "Last Month Expired"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None  # Hide the add button from list view header

    list_display = (
        "reference_id",
        "customer",
        "get_amc_type_display",
        # "amcname",  # Commented out - not needed
        "current_status",
        "contract_period",
        "amount_details",
    )

    list_export = [
        "id",
        "reference_id",
        "customer",
        # "amcname",  # Commented out - not needed
        "latitude",
        "equipment_no",
        "invoice_frequency",
        "amc_type",
        "payment_terms",
        "start_date_str",
        "end_date_str",
        "notes",
        "is_generate_contract",
        "no_of_services",
        "price",
        "no_of_lifts",
        "gst_percentage",
        "total",
        "contract_amount",
        "total_amount_paid",
        "amount_due",
        "amc_service_item",
        "status",
        "created_str",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "reference_id",
        # "amcname",  # Commented out - not needed
        "customer__site_name",
        "equipment_no",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        first_of_this_month = today.replace(day=1)
        last_month_last_day = first_of_this_month - timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)
        return AMC.objects.filter(end_date__gte=last_month_first_day, end_date__lte=last_month_last_day).order_by("end_date")
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add/edit/delete permissions"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddAMCExpiringPermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding/editing/deleting AMC expiring records"""
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddAMCExpiringPermissionPolicy(self.model)


class AMCExpiringNextMonthViewSet(SnippetViewSet):
    model = AMCExpiringNextMonth
    icon = "date"
    menu_label = "Next Month Expiring"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None  # Hide the add button from list view header

    list_display = (
        "reference_id",
        "customer",
        "get_amc_type_display",
        # "amcname",  # Commented out - not needed
        "current_status",
        "contract_period",
        "amount_details",
    )

    list_export = [
        "id",
        "reference_id",
        "customer",
        # "amcname",  # Commented out - not needed
        "latitude",
        "equipment_no",
        "invoice_frequency",
        "amc_type",
        "payment_terms",
        "start_date",
        "end_date",
        "notes",
        "is_generate_contract",
        "no_of_services",
        "price",
        "no_of_lifts",
        "gst_percentage",
        "total",
        "contract_amount",
        "total_amount_paid",
        "amount_due",
        "amc_service_item",
        "status",
        "created",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "reference_id",
        # "amcname",  # Commented out - not needed
        "customer__site_name",
        "equipment_no",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        if today.month == 12:
            next_month_first = date(today.year + 1, 1, 1)
        else:
            next_month_first = date(today.year, today.month + 1, 1)
        if next_month_first.month == 12:
            month_after_next_first = next_month_first.replace(year=next_month_first.year + 1, month=1, day=1)
        else:
            month_after_next_first = next_month_first.replace(month=next_month_first.month + 1, day=1)
        next_month_last = month_after_next_first - timedelta(days=1)
        return AMC.objects.filter(end_date__gte=next_month_first, end_date__lte=next_month_last).order_by("end_date")
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add/edit/delete permissions"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddAMCExpiringPermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding/editing/deleting AMC expiring records"""
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddAMCExpiringPermissionPolicy(self.model)

class AMCManagementGroup(SnippetViewSetGroup):
    items = (
        AMCViewSet,
        AMCExpiringThisMonthViewSet,  # Hidden from menu via wagtail_hooks
        AMCExpiringLastMonthViewSet,  # Hidden from menu via wagtail_hooks
        AMCExpiringNextMonthViewSet,  # Hidden from menu via wagtail_hooks
        AMCTypeViewSet,
        PaymentTermsViewSet,
    )
    menu_icon = "calendar"
    menu_label = "AMC "
    menu_name = "amc"
    menu_order = 4


register_snippet(AMCManagementGroup)
