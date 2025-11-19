from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from django.urls import reverse
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
import re


# ======================================================
#  SNIPPET MODELS
# ======================================================

class FloorID(models.Model):
    value = models.CharField(max_length=10, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class Brand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class MachineType(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class MachineBrand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class DoorType(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class DoorBrand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class LiftType(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class ControllerBrand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


class Cabin(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]
    def __str__(self):
        return self.value


# ======================================================
#  MAIN MODEL
# ======================================================

class Lift(models.Model):
    reference_id = models.CharField(max_length=20, unique=True, editable=False, null=False, blank=False)
    lift_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    floor_id = models.ForeignKey(FloorID, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    model = models.CharField(max_length=100)
    no_of_passengers = models.PositiveIntegerField()
    load_kg = models.PositiveIntegerField(blank=True, null=True)
    speed = models.CharField(max_length=50)
    lift_type = models.ForeignKey(LiftType, on_delete=models.SET_NULL, null=True)
    machine_type = models.ForeignKey(MachineType, on_delete=models.SET_NULL, null=True)
    machine_brand = models.ForeignKey(MachineBrand, on_delete=models.SET_NULL, null=True)
    door_type = models.ForeignKey(DoorType, on_delete=models.SET_NULL, null=True)
    door_brand = models.ForeignKey(DoorBrand, on_delete=models.SET_NULL, null=True)
    controller_brand = models.ForeignKey(ControllerBrand, on_delete=models.SET_NULL, null=True)
    cabin = models.ForeignKey(Cabin, on_delete=models.SET_NULL, null=True)
    block = models.CharField(max_length=50, blank=True, null=True)
    license_no = models.CharField(max_length=50, blank=True, null=True)
    license_start_date = models.DateField(blank=True, null=True)
    license_end_date = models.DateField(blank=True, null=True)

    panels = [
        FieldPanel("reference_id"),
        FieldPanel("lift_code"),
        FieldPanel("name"),
        FieldPanel("price"),
        FieldPanel("floor_id"),
        FieldPanel("brand"),
        FieldPanel("model"),
        FieldPanel("no_of_passengers"),
        FieldPanel("load_kg"),
        FieldPanel("speed"),
        FieldPanel("lift_type"),
        FieldPanel("machine_type"),
        FieldPanel("machine_brand"),
        FieldPanel("door_type"),
        FieldPanel("door_brand"),
        FieldPanel("controller_brand"),
        FieldPanel("cabin"),
        FieldPanel("block"),
        FieldPanel("license_no"),
        FieldPanel("license_start_date"),
        FieldPanel("license_end_date"),
    ]

    def clean(self):
        """Validate lift fields"""
        super().clean()
        
        # Validate lift_code is required
        if not self.lift_code or self.lift_code.strip() == '':
            raise ValidationError({
                'lift_code': 'Lift Code is required. Please enter a lift code.'
            })
        
        # Validate floor_id is required
        if not self.floor_id:
            raise ValidationError({
                'floor_id': 'Floor ID is required. Please select a floor ID.'
            })
        
        # Validate brand is required
        if not self.brand:
            raise ValidationError({
                'brand': 'Brand is required. Please select a brand.'
            })
        
        # Validate lift_type is required
        if not self.lift_type:
            raise ValidationError({
                'lift_type': 'Lift Type is required. Please select a lift type.'
            })
        
        # Validate machine_type is required
        if not self.machine_type:
            raise ValidationError({
                'machine_type': 'Machine Type is required. Please select a machine type.'
            })
        
        # Validate door_type is required
        if not self.door_type:
            raise ValidationError({
                'door_type': 'Door Type is required. Please select a door type.'
            })
        
        if self.name:
            # Allow letters, numbers, spaces, and hyphens
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', self.name):
                raise ValidationError({
                    'name': 'Name must not contain special characters. Only letters, numbers, spaces, and hyphens are allowed.'
                })
        
        if self.model:
            # Allow letters, numbers, spaces, and hyphens
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', self.model):
                raise ValidationError({
                    'model': 'Model must not contain special characters. Only letters, numbers, spaces, and hyphens are allowed.'
                })
        
        if self.speed:
            # Ensure speed is not just whitespace
            if self.speed.strip() == '':
                raise ValidationError({
                    'speed': 'Speed cannot be empty or contain only whitespace.'
                })
            
            # Validate length (max 50 characters)
            if len(self.speed) > 50:
                raise ValidationError({
                    'speed': 'Speed must not exceed 50 characters.'
                })
            
            # Allow letters, numbers, spaces, hyphens, and forward slashes
            if not re.match(r'^[a-zA-Z0-9\s\-/]+$', self.speed):
                raise ValidationError({
                    'speed': 'Speed must not contain special characters. Only letters, numbers, spaces, hyphens, and forward slashes are allowed.'
                })
    
    def save(self, *args, **kwargs):
        """Call clean before saving"""
        self.full_clean()
        if not self.reference_id:
            # Generate reference ID in format: LIFT-YYYY-NNNN
            import datetime
            year = datetime.datetime.now().year
            # Get the count of lifts created this year and add 1
            count = Lift.objects.filter(
                reference_id__startswith=f'LIFT-{year}-'
            ).count() + 1
            self.reference_id = f'LIFT-{year}-{count:04d}'

        if self.no_of_passengers and (self.load_kg is None or self.load_kg == 0):
            self.load_kg = int(self.no_of_passengers) * 68
        super().save(*args, **kwargs)

    def __str__(self):
        if self.lift_code:
            return f"{self.lift_code} - {self.name}"
        else:
            return f"{self.reference_id} - {self.name}"

    def passengers_display(self):
        return f"{self.no_of_passengers} Persons"
    passengers_display.short_description = "No. of Passengers"

    # Helper methods for export (return string values for ForeignKey fields)
    def floor_id_value(self):
        return self.floor_id.value if self.floor_id else ""
    floor_id_value.short_description = "Floor ID"

    def brand_value(self):
        return self.brand.value if self.brand else ""
    brand_value.short_description = "Brand"

    def lift_type_value(self):
        return self.lift_type.value if self.lift_type else ""
    lift_type_value.short_description = "Lift Type"

    def machine_type_value(self):
        return self.machine_type.value if self.machine_type else ""
    machine_type_value.short_description = "Machine Type"

    def machine_brand_value(self):
        return self.machine_brand.value if self.machine_brand else ""
    machine_brand_value.short_description = "Machine Brand"

    def door_type_value(self):
        return self.door_type.value if self.door_type else ""
    door_type_value.short_description = "Door Type"

    def door_brand_value(self):
        return self.door_brand.value if self.door_brand else ""
    door_brand_value.short_description = "Door Brand"

    def controller_brand_value(self):
        return self.controller_brand.value if self.controller_brand else ""
    controller_brand_value.short_description = "Controller Brand"

    def cabin_value(self):
        return self.cabin.value if self.cabin else ""
    cabin_value.short_description = "Cabin"

    # Helper methods for date export (format as YYYY-MM-DD for bulk import compatibility)
    def license_start_date_str(self):
        """Return license_start_date as YYYY-MM-DD string for export"""
        if self.license_start_date:
            return self.license_start_date.strftime('%Y-%m-%d')
        return ""
    license_start_date_str.short_description = "License Start Date"

    def license_end_date_str(self):
        """Return license_end_date as YYYY-MM-DD string for export"""
        if self.license_end_date:
            return self.license_end_date.strftime('%Y-%m-%d')
        return ""
    license_end_date_str.short_description = "License End Date"


# Proxy model for Bulk Import menu item (not used for actual data)
class BulkImportLift(Lift):
    """Proxy model used only for menu structure - redirects to bulk import view"""
    class Meta:
        proxy = True
        verbose_name = "Bulk Import"
        verbose_name_plural = "Bulk Import"


# ======================================================
#  SNIPPET VIEWSETS
# ======================================================

class LiftViewSet(SnippetViewSet):
    model = Lift
    icon = "cog"
    menu_label = "All Lifts"
    inspect_view_enabled = True

    def get_form_class(self):
        from django.forms import ModelForm

        class LiftForm(ModelForm):
            class Meta:
                model = Lift
                exclude = ('reference_id',)

        return LiftForm

    list_display = (
        "reference_id",
        "lift_code",
        "passengers_display",
        "brand",
        "load_kg",
        "lift_type",
        "machine_type",
        "door_type",
        "floor_id",
    )

    # Export ALL lift fields for XLSX/CSV download
    list_export = (
        'reference_id',
        'lift_code',
        'name',
        'price',
        'floor_id_value',
        'brand_value',
        'model',
        'no_of_passengers',
        'load_kg',
        'speed',
        'lift_type_value',
        'machine_type_value',
        'machine_brand_value',
        'door_type_value',
        'door_brand_value',
        'controller_brand_value',
        'cabin_value',
        'block',
        'license_no',
        'license_start_date_str',
        'license_end_date_str',
    )
    
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "reference_id",
        "lift_code",
        "brand__value",
        "lift_type__value",
        "machine_type__value",
        "door_type__value",
        "floor_id__value",
    )

    list_filter = (
        "brand",
        "lift_type",
        "machine_type",
        "door_type",
        "floor_id",
    )

    def get_add_url(self):
        return reverse("add_lift_custom")

    def get_edit_url(self, instance):
        # Use reference_id if lift_code is not available
        identifier = instance.lift_code if instance.lift_code else instance.reference_id
        return reverse("edit_lift_custom", args=(identifier,))

    def add_view(self, request):
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            # Check if this is an export request
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                # Only allow superusers to export
                if not request.user.is_superuser:
                    # Show in-page error instead of a blank 403 page
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export lifts.")
                    # Redirect back to the list view without the export param
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)
    
    index_view_class = RestrictedIndexView


# Custom ViewSet for Bulk Import
class BulkImportViewSet(SnippetViewSet):
    """Custom ViewSet for Bulk Import Lifts"""
    model = BulkImportLift
    menu_label = "Bulk Import"
    icon = "download"
    menu_order = 200
    add_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    inspect_view_enabled = False
    
    def get_form_class(self, for_update=False):
        from django.forms import ModelForm
        # Exclude reference_id as it's non-editable
        class BulkImportLiftForm(ModelForm):
            class Meta:
                model = BulkImportLift
                exclude = ('reference_id',)
        return BulkImportLiftForm
    
    # Override the index view to show bulk import page
    class BulkImportIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            # Redirect to bulk import view instead of showing list
            from django.shortcuts import render
            from lift import views
            return views.bulk_import_view(request)
    
    index_view_class = BulkImportIndexView


# ============== Other snippet ViewSets ==============

class FloorIDViewSet(SnippetViewSet):
    model = FloorID
    icon = "list-ul"
    menu_label = "Floor IDs"


class BrandViewSet(SnippetViewSet):
    model = Brand
    icon = "tag"
    menu_label = "Brands"


class MachineTypeViewSet(SnippetViewSet):
    model = MachineType
    icon = "cog"
    menu_label = "Machine Types"


class MachineBrandViewSet(SnippetViewSet):
    model = MachineBrand
    icon = "cog"
    menu_label = "Machine Brands"


class DoorTypeViewSet(SnippetViewSet):
    model = DoorType
    icon = "cog"
    menu_label = "Door Types"


class DoorBrandViewSet(SnippetViewSet):
    model = DoorBrand
    icon = "cog"
    menu_label = "Door Brands"


class LiftTypeViewSet(SnippetViewSet):
    model = LiftType
    icon = "cog"
    menu_label = "Lift Types"


class ControllerBrandViewSet(SnippetViewSet):
    model = ControllerBrand
    icon = "cog"
    menu_label = "Controller Brands"


class CabinViewSet(SnippetViewSet):
    model = Cabin
    icon = "cog"
    menu_label = "Cabins"


# ======================================================
#  GROUP
# ======================================================

class LiftGroup(SnippetViewSetGroup):
    items = (
        LiftViewSet,
        BulkImportViewSet,
        FloorIDViewSet,
        BrandViewSet,
        MachineTypeViewSet,
        MachineBrandViewSet,
        DoorTypeViewSet,
        DoorBrandViewSet,
        LiftTypeViewSet,
        ControllerBrandViewSet,
        CabinViewSet,
    )
    menu_icon = "cog"
    menu_label = "Lift"
    menu_name = "lift"
    menu_order = 2


register_snippet(LiftGroup)
