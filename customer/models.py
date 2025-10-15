from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


# ---------- SNIPPET MODELS ----------

class Route(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


class Branch(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


class ProvinceState(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# ---------- MAIN MODEL ----------

SECTOR_CHOICES = (
    ('government', 'Government'),
    ('private', 'Private'),
)


class Customer(models.Model):
    # --- Basic Info ---
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    site_id = models.CharField(max_length=30)
    job_no = models.CharField(max_length=50, blank=True, unique=True)
    site_name = models.CharField(max_length=100)
    site_address = models.TextField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True, unique=True)
    office_address = models.TextField(blank=True)

    # --- Contact Person ---
    contact_person_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True)

    # --- Location Info ---
    pin_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, blank=True)
    province_state = models.ForeignKey(ProvinceState, on_delete=models.SET_NULL, null=True)
    city = models.CharField(max_length=100)
    sector = models.CharField(
        max_length=20, choices=SECTOR_CHOICES, default='private', blank=True, null=True
    )
    routes = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    handover_date = models.DateField(null=True, blank=True)
    billing_name = models.CharField(max_length=100, blank=True)
    uploads_files = models.FileField(upload_to='customer_uploads/', null=True, blank=True, max_length=100)

    # --- Admin Panels ---
    panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            FieldPanel("site_id"),
            FieldPanel("job_no"),
            FieldPanel("site_name"),
            FieldPanel("site_address"),
            FieldPanel("email"),
            FieldPanel("phone"),
            FieldPanel("mobile"),
            FieldPanel("office_address"),
        ], heading="Basic Details"),

        MultiFieldPanel([
            FieldPanel("contact_person_name"),
            FieldPanel("designation"),
        ], heading="Contact Person"),

        MultiFieldPanel([
            FieldPanel("pin_code"),
            FieldPanel("country"),
            FieldPanel("province_state"),
            FieldPanel("city"),
            FieldPanel("sector"),
            FieldPanel("routes"),
            FieldPanel("branch"),
            FieldPanel("handover_date"),
            FieldPanel("billing_name"),
            FieldPanel("uploads_files"),
        ], heading="Location & Other Info"),
    ]

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.site_name} ({self.reference_id})"

    # --- Auto-generate reference_id ---
    def save(self, *args, **kwargs):
        if not self.reference_id:
            last_customer = Customer.objects.all().order_by('id').last()
            if last_customer and last_customer.reference_id.startswith('CUST'):
                try:
                    last_id = int(last_customer.reference_id.replace('CUST', ''))
                except ValueError:
                    last_id = 0
                self.reference_id = f'CUST{str(last_id + 1).zfill(3)}'
            else:
                self.reference_id = 'CUST001'
        super().save(*args, **kwargs)

    # --- Computed (fetched) fields ---
    @property
    def pan_number(self):
        return "Fetched PAN1234"

    @property
    def gst_number(self):
        return "Fetched GST5678"

    @property
    def active_mobile(self):
        return 5

    @property
    def expired_mobile(self):
        return 2

    @property
    def contracts(self):
        return 3

    @property
    def no_of_lifts(self):
        return 4

    @property
    def completed_services(self):
        return 10

    @property
    def due_services(self):
        return 1

    @property
    def overdue_services(self):
        return 0

    @property
    def tickets(self):
        return 6


# ---------- SNIPPET VIEWSETS ----------

class RouteViewSet(SnippetViewSet):
    model = Route
    icon = "route"
    menu_label = "Routes"


class BranchViewSet(SnippetViewSet):
    model = Branch
    icon = "building"
    menu_label = "Branches"


class ProvinceStateViewSet(SnippetViewSet):
    model = ProvinceState
    icon = "map"
    menu_label = "Provinces / States"


class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    menu_label = "Customers"
    inspect_view_enabled = True
    list_display = (
        "reference_id", "site_name", "site_id", "email", "phone",
        "city", "branch", "routes", "sector",
    )
    list_export = (
        "reference_id", "site_name", "site_id", "email", "phone",
        "city", "branch", "routes", "sector",
    )


# ---------- GROUP ----------

class CustomerGroup(SnippetViewSetGroup):
    items = (
        RouteViewSet,
        BranchViewSet,
        ProvinceStateViewSet,
        CustomerViewSet,
    )
    icon = "folder-user"
    menu_label = "Customer Management"
    menu_name = "customer_management"


# ---------- REGISTER GROUP ----------

register_snippet(CustomerGroup)
