from django.db import models
from datetime import date, timedelta
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import your Lift model
from lift.models import Lift  # 👈 replace "lift_app" with your actual lift app name


# ======================================================
#  SNIPPET MODELS
# ======================================================

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


# ======================================================
#  CUSTOMER MODEL
# ======================================================

SECTOR_CHOICES = (
    ('government', 'Government'),
    ('private', 'Private'),
)

class Customer(models.Model):
    reference_id = models.CharField(max_length=10, unique=True, editable=False)
    site_id = models.CharField(max_length=30)
    job_no = models.CharField(max_length=50, blank=True, unique=True)
    site_name = models.CharField(max_length=100)
    site_address = models.TextField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True, unique=True)
    office_address = models.TextField(blank=True)

    contact_person_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True)

    pin_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    province_state = models.ForeignKey(ProvinceState, on_delete=models.SET_NULL, null=True)
    city = models.CharField(max_length=100)
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES, default='private', blank=True, null=True)
    routes = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    handover_date = models.DateField(null=True, blank=True)
    billing_name = models.CharField(max_length=100, blank=True, null=True)
    uploads_files = models.FileField(upload_to='customer_uploads/', null=True, blank=True, max_length=100)

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


# ======================================================
#  CUSTOMER LICENSE MODEL (AUTO-FETCHED)
# ======================================================

def one_year_from_today():
    return date.today() + timedelta(days=365)



class CustomerLicense(models.Model):
    license_no = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="licenses")
    lift = models.ForeignKey(Lift, on_delete=models.CASCADE, related_name="licenses")
    period_start = models.DateField(default=date.today)
    period_end = models.DateField(default=one_year_from_today)

    def save(self, *args, **kwargs):
        if not self.license_no:
            last = CustomerLicense.objects.all().order_by("id").last()
            next_id = 1 if not last else last.id + 1
            self.license_no = f"LIC{next_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.license_no} ({self.customer.site_name} - {self.lift.lift_code})"

    @property
    def status(self):
        return "Active" if self.period_end >= date.today() else "Expired"

    def lift_details(self):
        lift = self.lift
        if not lift:
            return "No lift linked"

        return (
            f"Code: {lift.lift_code} | "
            f"Name: {lift.name} | "
            f"Floor: {getattr(lift.floor_id, 'value', 'N/A')} | "
            f"Brand: {getattr(lift.brand, 'value', 'N/A')} | "
            f"Machine: {getattr(lift.machine_type, 'value', 'N/A')} / {getattr(lift.machine_brand, 'value', 'N/A')} | "
            f"Door: {getattr(lift.door_type, 'value', 'N/A')} / {getattr(lift.door_brand, 'value', 'N/A')} | "
            f"Controller: {getattr(lift.controller_brand, 'value', 'N/A')} | "
            f"Cabin: {getattr(lift.cabin, 'value', 'N/A')} | "
            f"Load: {lift.load_kg} Kg | "
            f"Speed: {lift.speed}"
        )


# ======================================================
#  AUTO-CREATE LICENSE LOGIC
# ======================================================

@receiver(post_save, sender=Customer)
def create_customer_license(sender, instance, **kwargs):
    """
    Auto-create CustomerLicense when Customer.job_no == Lift.lift_code
    """
    if instance.job_no:
        try:
            lift = Lift.objects.get(lift_code=instance.job_no)
            exists = CustomerLicense.objects.filter(customer=instance, lift=lift).exists()
            if not exists:
                CustomerLicense.objects.create(
                    customer=instance,
                    lift=lift,
                    period_start=date.today(),
                    period_end=one_year_from_today(),
                )
        except Lift.DoesNotExist:
            pass


# ======================================================
#  WAGTAIL ADMIN VIEWSETS
# ======================================================

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
    list_display = ("reference_id", "site_name", "site_id", "email", "phone", "city", "branch", "routes", "sector")
    list_export = ("reference_id", "site_name", "site_id", "email", "phone", "city", "branch", "routes", "sector")


# -------- LICENSE VIEWSET (READ ONLY) --------
class CustomerLicenseViewSet(SnippetViewSet):
    model = CustomerLicense
    icon = "doc-full"
    menu_label = "Customer Licenses"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False

    list_display = ("license_no", "customer", "lift_details", "period_start", "period_end", "status")
    list_export = ("license_no", "customer", "lift_details", "period_start", "period_end", "status")

    # ✅ Custom method to show full lift details
    def lift_details(self, obj):
        lift = obj.lift
        if not lift:
            return "No lift linked"

        # build readable info string
        return (
            f"Code: {lift.lift_code} | "
            f"Name: {lift.name} | "
            f"Floor: {getattr(lift.floor_id, 'value', 'N/A')} | "
            f"Brand: {getattr(lift.brand, 'value', 'N/A')} | "
            f"Machine: {getattr(lift.machine_type, 'value', 'N/A')} / {getattr(lift.machine_brand, 'value', 'N/A')} | "
            f"Door: {getattr(lift.door_type, 'value', 'N/A')} / {getattr(lift.door_brand, 'value', 'N/A')} | "
            f"Controller: {getattr(lift.controller_brand, 'value', 'N/A')} | "
            f"Cabin: {getattr(lift.cabin, 'value', 'N/A')} | "
            f"Load: {lift.load_kg} Kg | "
            f"Speed: {lift.speed}"
        )

    lift_details.short_description = "Lift Details"

# ======================================================
#  GROUPS
# ======================================================

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


class CustomerLicenseGroup(SnippetViewSetGroup):
    items = (CustomerLicenseViewSet,)
    icon = "folder-open-inverse"
    menu_label = "Customer License Management"
    menu_name = "customer_license_management"


# ======================================================
#  REGISTER
# ======================================================

register_snippet(CustomerGroup)
register_snippet(CustomerLicenseGroup)
