from django.db import models
from datetime import date, timedelta
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.db.models.signals import post_save
from django.dispatch import receiver


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
#  MAIN MODEL: CUSTOMER
# ======================================================

SECTOR_CHOICES = (
    ('government', 'Government'),
    ('private', 'Private'),
)


def one_year_from_today():
    """Helper for one-year default license period."""
    return date.today() + timedelta(days=365)


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
    same_as_site_address = models.BooleanField(default=False, help_text="Check to set office address same as site address")

    contact_person_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True)

    pin_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    province_state = models.ForeignKey("ProvinceState", on_delete=models.SET_NULL, null=True)
    city = models.CharField(max_length=100)
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES, default='private', blank=True, null=True)
    routes = models.ForeignKey("Route", on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True)
    handover_date = models.DateField(null=True, blank=True)
    billing_name = models.CharField(max_length=100, blank=True, null=True)
    uploads_files = models.FileField(upload_to='customer_uploads/', null=True, blank=True, max_length=100)

    generate_license_now = models.BooleanField(default=False)

    panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            FieldPanel("site_id"),
            FieldPanel("job_no"),
            FieldPanel("site_name"),
            FieldPanel("site_address"),
            FieldPanel("same_as_site_address"),
            FieldPanel("office_address"),
            FieldPanel("email"),
            FieldPanel("phone"),
            FieldPanel("mobile"),
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

        MultiFieldPanel([
            FieldPanel("generate_license_now"),
        ], heading="License Generation"),
    ]

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.site_name} - {self.job_no}" if self.job_no else self.site_name

    def save(self, *args, **kwargs):
        # Auto-generate reference ID
        if not self.reference_id:
            last = Customer.objects.order_by('id').last()
            if last and last.reference_id.startswith('CUST'):
                try:
                    next_id = int(last.reference_id.replace('CUST', '')) + 1
                except ValueError:
                    next_id = 1
            else:
                next_id = 1
            self.reference_id = f'CUST{next_id:03d}'

        # Office address sync
        if self.same_as_site_address:
            self.office_address = self.site_address

        super().save(*args, **kwargs)

        # License auto-generation (Customer added first)
        if self.generate_license_now and self.job_no:
            try:
                from lift.models import Lift
                lift = Lift.objects.filter(lift_code=self.job_no).first()
                if lift:
                    from customer.models import CustomerLicense
                    if not CustomerLicense.objects.filter(customer=self, lift=lift).exists():
                        CustomerLicense.objects.create(
                            customer=self,
                            lift=lift,
                            period_start=lift.license_start_date or date.today(),
                            period_end=lift.license_end_date or one_year_from_today(),
                        )
            except Exception:
                pass

        # Reset checkbox without recursion
        if self.generate_license_now:
            Customer.objects.filter(pk=self.pk).update(generate_license_now=False)


# ======================================================
#  CUSTOMER LICENSE MODEL (AUTO-GENERATED)
# ======================================================

class CustomerLicense(models.Model):
    license_no = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="licenses")
    lift = models.ForeignKey("lift.Lift", on_delete=models.CASCADE, related_name="licenses")
    period_start = models.DateField(default=date.today)
    period_end = models.DateField(default=one_year_from_today)

    panels = [
        FieldPanel("license_no", read_only=True),
        FieldPanel("customer"),
        FieldPanel("lift"),
        FieldPanel("period_start"),
        FieldPanel("period_end"),
    ]

    def save(self, *args, **kwargs):
        if not self.license_no:
            last = CustomerLicense.objects.order_by("id").last()
            next_id = (last.id + 1) if last else 1
            self.license_no = f"LIC{next_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.license_no} ({self.customer.site_name} - {self.lift.lift_code})"

    @property
    def status(self):
        return "Active" if self.period_end >= date.today() else "Expired"

    @property
    def lift_details(self):
        lift = self.lift
        if not lift:
            return "No lift linked"
        return (
            f"Code: {lift.lift_code} | Name: {lift.name} | Floor: {getattr(lift.floor_id, 'value', 'N/A')} | "
            f"Brand: {getattr(lift.brand, 'value', 'N/A')} | Machine: {getattr(lift.machine_type, 'value', 'N/A')} / "
            f"{getattr(lift.machine_brand, 'value', 'N/A')} | Door: {getattr(lift.door_type, 'value', 'N/A')} / "
            f"{getattr(lift.door_brand, 'value', 'N/A')} | Controller: {getattr(lift.controller_brand, 'value', 'N/A')} | "
            f"Cabin: {getattr(lift.cabin, 'value', 'N/A')} | Load: {lift.load_kg} Kg | Speed: {lift.speed}"
        )


# ======================================================
#  AUTO LICENSE GENERATION (LIFT FIRST LOGIC)
# ======================================================

@receiver(post_save, sender="lift.Lift")
def auto_create_license_from_lift(sender, instance, created, **kwargs):
    """If a Lift is added or updated before Customer, generate license when job_no matches."""
    from customer.models import CustomerLicense
    customer = Customer.objects.filter(job_no=instance.lift_code).first()
    if not customer:
        return

    existing_license = CustomerLicense.objects.filter(customer=customer, lift=instance).first()
    if existing_license:
        # Keep license period in sync with lift
        existing_license.period_start = instance.license_start_date or existing_license.period_start
        existing_license.period_end = instance.license_end_date or existing_license.period_end
        existing_license.save()
    else:
        CustomerLicense.objects.create(
            customer=customer,
            lift=instance,
            period_start=instance.license_start_date or date.today(),
            period_end=instance.license_end_date or one_year_from_today(),
        )


# ======================================================
#  WAGTAIL ADMIN VIEWSETS
# ======================================================

class RouteViewSet(SnippetViewSet):
    model = Route
    icon = "form"
    menu_label = "Routes"


class BranchViewSet(SnippetViewSet):
    model = Branch
    icon = "pick"
    menu_label = "Branches"


class ProvinceStateViewSet(SnippetViewSet):
    model = ProvinceState
    icon = "site"
    menu_label = "Provinces / States"


class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    menu_label = "Customers"
    inspect_view_enabled = True
    list_display = (
        "reference_id", "site_name", "job_no", "email", "phone", "city", "branch", "routes", "sector",
    )
    list_export = list_display


class CustomerLicenseViewSet(SnippetViewSet):
    model = CustomerLicense
    icon = "doc-full"
    menu_label = "Customer Licenses"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display = ("license_no", "customer", "lift_details", "period_start", "period_end", "status")
    list_export = list_display


# ======================================================
#  WAGTAIL GROUPS
# ======================================================

class CustomerGroup(SnippetViewSetGroup):
    items = (CustomerViewSet, RouteViewSet, BranchViewSet, ProvinceStateViewSet)
    menu_icon = "group"
    menu_label = "Customer"
    menu_name = "customer"


class CustomerLicenseGroup(SnippetViewSetGroup):
    items = (CustomerLicenseViewSet,)
    menu_icon = "doc-full"
    menu_label = "Customer License"
    menu_name = "customer_license"


# ======================================================
#  REGISTER GROUPS
# ======================================================

register_snippet(CustomerGroup)
register_snippet(CustomerLicenseGroup)
