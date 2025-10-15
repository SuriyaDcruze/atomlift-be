from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


# ---------- SNIPPETS ----------
# @register_snippet
class FloorID(models.Model):
    value = models.CharField(max_length=10, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class Brand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class MachineType(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class MachineBrand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class DoorType(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class DoorBrand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class LiftType(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class ControllerBrand(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# @register_snippet
class Cabin(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# ---------- MAIN MODEL ----------
# @register_snippet
class Lift(models.Model):
    lift_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    floor_id = models.ForeignKey(FloorID, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    model = models.CharField(max_length=100)
    no_of_passengers = models.CharField(max_length=50)
    load_kg = models.CharField(max_length=50)
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

    def __str__(self):
        return f"{self.lift_code} - {self.name}"
    

# ---------- SNIPPET VIEWSETS ----------
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
    icon = "factory"
    menu_label = "Machine Brands"


class DoorTypeViewSet(SnippetViewSet):
    model = DoorType
    icon = "door"
    menu_label = "Door Types"


class DoorBrandViewSet(SnippetViewSet):
    model = DoorBrand
    icon = "package"
    menu_label = "Door Brands"


class LiftTypeViewSet(SnippetViewSet):
    model = LiftType
    icon = "chevron-up"
    menu_label = "Lift Types"


class ControllerBrandViewSet(SnippetViewSet):
    model = ControllerBrand
    icon = "cpu"
    menu_label = "Controller Brands"


class CabinViewSet(SnippetViewSet):
    model = Cabin
    icon = "box"
    menu_label = "Cabins"


class LiftViewSet(SnippetViewSet):
    model = Lift
    icon = "archive"
    menu_label = "Lifts"
    inspect_view_enabled = True
    list_export = (
        'lift_code', 'brand', 'model', 'no_of_passengers', 'load_kg', 'speed', 'lift_type', 'machine_type', 'machine_brand', 'door_type', 'door_brand', 'controller_brand', 'cabin', 'block', 'license_no', 'license_start_date', 'license_end_date')


# ---------- GROUP ----------
class LiftGroup(SnippetViewSetGroup):
    items = (
        FloorIDViewSet,
        BrandViewSet,
        MachineTypeViewSet,
        MachineBrandViewSet,
        DoorTypeViewSet,
        DoorBrandViewSet,
        LiftTypeViewSet,
        ControllerBrandViewSet,
        CabinViewSet,
        LiftViewSet,
    )
    icon = "folder-inverse"
    menu_label = "Lift Management"
    menu_name = "lift_management"

register_snippet(LiftGroup)