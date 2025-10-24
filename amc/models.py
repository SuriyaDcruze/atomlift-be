from django.db import models
from django.utils import timezone
from datetime import timedelta
from datetime import date
from decimal import Decimal
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList

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
    amcname = models.CharField(max_length=100, blank=True)
    latitude = models.CharField(max_length=255, blank=True, null=True)      # site address
    equipment_no = models.CharField(max_length=50, blank=True, null=True)   # job no
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
    amc_type = models.ForeignKey(AMCType, on_delete=models.SET_NULL, null=True, blank=True)
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

    def save(self, *args, **kwargs):
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

    def __str__(self):
        return self.reference_id

    # Wagtail panels
    basic_panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            FieldPanel("customer"),
            FieldPanel("amcname"),
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
    menu_label = "AMC Types"
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

    # 👇 Columns shown in admin list
    list_display = (
        "reference_id",
        "customer",
        "amcname",
        "status",
        "start_date",
        "end_date",
        "amount_due",
    )

    # 👇 Export ALL model fields to CSV & XLSX
    list_export = [
        "id",
        "reference_id",
        "customer",
        "amcname",
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

    # 👇 Searchable fields
    search_fields = (
        "reference_id",
        "amcname",
        "customer__site_name",
        "equipment_no",
    )

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

    list_display = (
        "reference_id",
        "customer",
        "amcname",
        "status",
        "start_date",
        "end_date",
        "amount_due",
    )

    list_export = [
        "id",
        "reference_id",
        "customer",
        "amcname",
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
        "amcname",
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


class AMCExpiringLastMonthViewSet(SnippetViewSet):
    model = AMCExpiringLastMonth
    icon = "date"
    menu_label = "Last Month Expired"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False

    list_display = (
        "reference_id",
        "customer",
        "amcname",
        "status",
        "start_date",
        "end_date",
        "amount_due",
    )

    list_export = [
        "id",
        "reference_id",
        "customer",
        "amcname",
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
        "amcname",
        "customer__site_name",
        "equipment_no",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        first_of_this_month = today.replace(day=1)
        last_month_last_day = first_of_this_month - timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)
        return AMC.objects.filter(end_date__gte=last_month_first_day, end_date__lte=last_month_last_day).order_by("end_date")


class AMCExpiringNextMonthViewSet(SnippetViewSet):
    model = AMCExpiringNextMonth
    icon = "date"
    menu_label = "Next Month Expiring"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False

    list_display = (
        "reference_id",
        "customer",
        "amcname",
        "status",
        "start_date",
        "end_date",
        "amount_due",
    )

    list_export = [
        "id",
        "reference_id",
        "customer",
        "amcname",
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
        "amcname",
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

class AMCManagementGroup(SnippetViewSetGroup):
    items = (
        AMCViewSet,
        AMCExpiringThisMonthViewSet,
        AMCExpiringLastMonthViewSet,
        AMCExpiringNextMonthViewSet,
        AMCTypeViewSet,
        PaymentTermsViewSet,
    )
    menu_icon = "calendar"
    menu_label = "AMC "
    menu_name = "amc"
    menu_order = 4


register_snippet(AMCManagementGroup)
