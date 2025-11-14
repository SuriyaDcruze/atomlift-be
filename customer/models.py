from django.db import models
from django.core.exceptions import ValidationError
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


class City(models.Model):
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
    # site_id = models.CharField(max_length=30)  # Don't need
    job_no = models.CharField(max_length=50, blank=True, unique=True)
    site_name = models.CharField(max_length=100)
    site_address = models.TextField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True, unique=True)
    office_address = models.TextField(blank=True)
    same_as_site_address = models.BooleanField(default=False, help_text="Check to set office address same as site address")

    contact_person_name = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True)

    pin_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    province_state = models.ForeignKey("ProvinceState", on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey("City", on_delete=models.SET_NULL, null=True, blank=True)
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES, default='private', blank=True, null=True)
    routes = models.ForeignKey("Route", on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True)
    handover_date = models.DateField(null=True, blank=True)
    billing_name = models.CharField(max_length=100, blank=True, null=True)
    uploads_files = models.FileField(upload_to='customer_uploads/', null=True, blank=True, max_length=100)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes for this customer")
    
    # Geographic coordinates (optional)
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Latitude coordinate (-90 to 90). Used for mapping and location services."
    )
    longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Longitude coordinate (-180 to 180). Used for mapping and location services."
    )

    generate_license_now = models.BooleanField(default=False)

    panels = [
        MultiFieldPanel([
            FieldPanel("reference_id", read_only=True),
            # FieldPanel("site_id"),  # Don't need
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
            FieldPanel("latitude"),
            FieldPanel("longitude"),
            FieldPanel("sector"),
            FieldPanel("routes"),
            FieldPanel("branch"),
            FieldPanel("handover_date"),
            FieldPanel("billing_name"),
            FieldPanel("uploads_files"),
            FieldPanel("notes"),
        ], heading="Location & Other Info"),

        MultiFieldPanel([
            FieldPanel("generate_license_now"),
        ], heading="License Generation"),
    ]

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def clean(self):
        """Validate latitude and longitude values"""
        super().clean()
        
        # Validate latitude range (-90 to 90)
        if self.latitude is not None:
            if self.latitude < -90 or self.latitude > 90:
                raise ValidationError({
                    'latitude': 'Latitude must be between -90 and 90 degrees.'
                })
        
        # Validate longitude range (-180 to 180)
        if self.longitude is not None:
            if self.longitude < -180 or self.longitude > 180:
                raise ValidationError({
                    'longitude': 'Longitude must be between -180 and 180 degrees.'
                })
        
        # If one coordinate is provided, recommend providing both
        if (self.latitude is not None and self.longitude is None) or \
           (self.latitude is None and self.longitude is not None):
            # This is just a warning, not an error, so we'll allow it
            pass

    def __str__(self):
        return f"{self.site_name} - {self.job_no}" if self.job_no else self.site_name

    def save(self, *args, **kwargs):
        # Validate before saving
        self.full_clean()
        
        # Auto-generate reference ID
        if not self.reference_id:
            last = Customer.objects.order_by('id').last()
            if last and last.reference_id.startswith('ATOM'):
                try:
                    next_id = int(last.reference_id.replace('ATOM', '')) + 1
                except ValueError:
                    next_id = 1
            else:
                next_id = 1
            self.reference_id = f'ATOM{next_id:03d}'

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
    
    def number_of_lifts(self):
        """Count the number of lifts assigned to this customer through licenses"""
        try:
            # Count lifts through CustomerLicense relationship
            return self.licenses.count()
        except Exception:
            return 0
    number_of_lifts.short_description = 'No. of Lifts'
    
    def number_of_routine_services(self):
        """Count the number of routine services for this customer"""
        try:
            from Routine_services.models import RoutineService
            return RoutineService.objects.filter(customer=self).count()
        except Exception:
            return 0
    number_of_routine_services.short_description = 'Routine Services'
    
    def number_of_invoices(self):
        """Count the number of invoices for this customer"""
        try:
            from invoice.models import Invoice
            return Invoice.objects.filter(customer=self).count()
        except Exception:
            return 0
    number_of_invoices.short_description = 'Invoices'


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
#  CUSTOMER CONTACT MODEL
# ======================================================

class CustomerContact(models.Model):
    """Contact information for a customer"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pin_code = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Contact"
        verbose_name_plural = "Customer Contacts"
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip() or f"Contact #{self.id}"


# ======================================================
#  CUSTOMER FEEDBACK MODEL
# ======================================================

SATISFACTION_CHOICES = (
    ('very_satisfied', 'Very Satisfied'),
    ('satisfied', 'Satisfied'),
    ('neutral', 'Neutral'),
    ('unsatisfied', 'Unsatisfied'),
    ('very_unsatisfied', 'Very Unsatisfied'),
)

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('reviewed', 'Reviewed'),
    ('resolved', 'Resolved'),
)

class CustomerFeedback(models.Model):
    """Feedback for a customer"""
    feedback_id = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="feedbacks")
    
    # Rating (1-5 stars)
    rating = models.IntegerField(default=0, help_text="Rating out of 5 stars")
    
    # Overall satisfaction ratings
    friendliness = models.CharField(max_length=20, choices=SATISFACTION_CHOICES, blank=True, null=True)
    knowledge = models.CharField(max_length=20, choices=SATISFACTION_CHOICES, blank=True, null=True)
    quickness = models.CharField(max_length=20, choices=SATISFACTION_CHOICES, blank=True, null=True)
    
    # Text feedback
    review = models.TextField(blank=True, null=True, help_text="Review/comment")
    improvement_suggestion = models.TextField(blank=True, null=True, help_text="How can we improve our service?")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Feedback"
        verbose_name_plural = "Customer Feedbacks"
        ordering = ['-created_date']

    def __str__(self):
        return f"Feedback {self.feedback_id} - {self.customer.site_name}"

    def save(self, *args, **kwargs):
        # Auto-generate feedback ID
        if not self.feedback_id:
            last = CustomerFeedback.objects.order_by('id').last()
            if last and last.feedback_id.startswith('FB'):
                try:
                    next_id = int(last.feedback_id.replace('FB', '')) + 1
                except ValueError:
                    next_id = 1
            else:
                next_id = 1
            self.feedback_id = f'FB{next_id:04d}'
        super().save(*args, **kwargs)


# ======================================================
#  CUSTOMER FOLLOW-UP MODEL
# ======================================================

class CustomerFollowUp(models.Model):
    """Follow-up entries for a customer"""
    followup_id = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="follow_ups")
    follow_up_date = models.DateField(help_text="Date for the follow-up")
    contact = models.ForeignKey(CustomerContact, on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_ups", help_text="Contact person for this follow-up")
    comment = models.TextField(blank=True, null=True, help_text="Comment/notes for the follow-up")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Follow-Up"
        verbose_name_plural = "Customer Follow-Ups"
        ordering = ['-follow_up_date', '-created_date']

    def __str__(self):
        contact_name = f"{self.contact.first_name} {self.contact.last_name or ''}".strip() if self.contact else "No Contact"
        return f"Follow-Up {self.followup_id} - {self.customer.site_name} ({contact_name})"

    def save(self, *args, **kwargs):
        # Auto-generate follow-up ID
        if not self.followup_id:
            last = CustomerFollowUp.objects.order_by('id').last()
            if last and last.followup_id.startswith('FU'):
                try:
                    next_id = int(last.followup_id.replace('FU', '')) + 1
                except ValueError:
                    next_id = 1
            else:
                next_id = 1
            self.followup_id = f'FU{next_id:04d}'
        super().save(*args, **kwargs)


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
    
    # Disable default edit view to use custom styled pages
    edit_view_enabled = False
    
    list_display = (
        "reference_id", "site_name", "job_no", "email", "phone", "number_of_lifts", "number_of_routine_services", "number_of_invoices",
    )
    list_export = ("reference_id", "site_name", "job_no", "email", "phone", "city__value", "branch__value", "routes__value", "sector")
    
    search_fields = (
        "reference_id",
        # "site_id",  # Don't need
        "site_name",
        "job_no",
        "email",
        "phone",
        "mobile",
        "contact_person_name",
        "city__value",
        "branch__value",
        "routes__value",
        "province_state__value",
    )
    
    list_filter = (
        "branch",
        "routes",
        "province_state",
        "city",
        "sector",
    )

    create_template_name = 'customer/add_customer_custom.html'
    inspect_template_name = 'customer/view_customer_custom.html'
    
    @property
    def add_url(self):
        """Override add URL to use custom styled page"""
        from django.urls import reverse
        return reverse('add_customer_custom')


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
    list_display_add_buttons = None  # Hide the add button from list view header
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add permission"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddCustomerLicensePermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding new customer licenses"""
            def user_has_permission(self, user, action):
                if action == "add":
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddCustomerLicensePermissionPolicy(self.model)


# ======================================================
#  WAGTAIL GROUPS
# ======================================================

class CustomerLicenseGroup(SnippetViewSetGroup):
    items = (CustomerLicenseViewSet,)
    menu_icon = "doc-full"
    menu_label = "Customer License"
    menu_name = "Customer_license"
    menu_order = 4

class CityViewSet(SnippetViewSet):
    model = City
    icon = "site"
    menu_label = "Cities"


class CustomerGroup(SnippetViewSetGroup):
    items = (CustomerViewSet, RouteViewSet, BranchViewSet, ProvinceStateViewSet, CityViewSet)
    menu_icon = "group"
    menu_label = "Customer"
    menu_name = "customer"




# ======================================================
#  REGISTER GROUPS
# ======================================================

# CustomerGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# CustomerLicenseGroup is still registered individually as it's not part of Sales
# Register CustomerGroup only through SalesGroup in home/wagtail_hooks.py
# Do NOT register it here
# register_snippet(CustomerGroup)

register_snippet(CustomerLicenseGroup)
