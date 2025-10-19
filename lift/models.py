from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.urls import reverse
from django.shortcuts import redirect


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
    license_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
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

    def save(self, *args, **kwargs):
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


# ======================================================
#  SNIPPET VIEWSETS
# ======================================================

class LiftViewSet(SnippetViewSet):
    model = Lift
    icon = "cog"
    menu_label = "Lifts"
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

    list_export = list_display

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
    menu_order = 1


register_snippet(LiftGroup)
