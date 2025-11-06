# models.py (corrected to include ViewSet overrides for custom add/edit redirection, added imports)
from django.db import models
from django.forms.widgets import RadioSelect
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.forms.widgets import RadioSelect
from django.urls import reverse
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
import re



# ---------- SNIPPET MODELS ----------
class Type(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


class Make(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


class Unit(models.Model):
    value = models.CharField(max_length=50, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# ---------- MAIN MODEL ----------
class Item(models.Model):
    item_number = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(max_length=100)
    make = models.ForeignKey(Make, on_delete=models.SET_NULL, null=True)
    model = models.CharField(max_length=100)
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True)
    capacity = models.CharField(max_length=50)
    threshold_qty = models.IntegerField(blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    service_type = models.CharField(
        max_length=10,
        choices=[('Goods', 'Goods'), ('Services', 'Services')],
        default='Goods',
    )
    tax_preference = models.CharField(
        max_length=15,
        choices=[('Taxable', 'Taxable'), ('Non-Taxable', 'Non-Taxable')],
        default='Non-Taxable',
    )
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    sac_code = models.CharField(max_length=10, blank=True, null=True)
    igst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    description = models.TextField(blank=True)

    panels = [
        MultiFieldPanel([
            FieldPanel("item_number", read_only=True),
            FieldPanel("name"),
            FieldPanel("make"),
            FieldPanel("model"),
            FieldPanel("type"),
            FieldPanel("capacity"),
            FieldPanel("threshold_qty"),
            FieldPanel("sale_price"),
            FieldPanel("purchase_price"),
        ], heading="Essential Information"),

        MultiFieldPanel([
            FieldPanel("service_type", widget=RadioSelect),
            FieldPanel("tax_preference", widget=RadioSelect),
        ], heading="Service & Tax Type"),

        MultiFieldPanel([
            FieldPanel("unit"),
            FieldPanel("sac_code"),
            FieldPanel("igst"),
            FieldPanel("gst"),
            FieldPanel("description"),
        ], heading="Tax & Additional Details"),
    ]

    def clean(self):
        """Validate that name does not contain special characters"""
        super().clean()
        
        if self.name:
            # Allow letters, numbers, spaces, and hyphens
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', self.name):
                raise ValidationError({
                    'name': 'Name must not contain special characters. Only letters, numbers, spaces, and hyphens are allowed.'
                })
        
        if self.capacity:
            # Ensure capacity is not just whitespace
            if self.capacity.strip() == '':
                raise ValidationError({
                    'capacity': 'Capacity cannot be empty or contain only whitespace.'
                })
            
            # Validate length (max 50 characters)
            if len(self.capacity) > 50:
                raise ValidationError({
                    'capacity': 'Capacity must not exceed 50 characters.'
                })
            
            # Allow letters, numbers, spaces, hyphens, and common capacity unit symbols (kg, lbs, tons, etc.)
            # Pattern allows: alphanumeric, spaces, hyphens, forward slashes, and common capacity indicators
            if not re.match(r'^[a-zA-Z0-9\s\-/]+$', self.capacity):
                raise ValidationError({
                    'capacity': 'Capacity must not contain special characters. Only letters, numbers, spaces, hyphens, and forward slashes are allowed.'
                })
    
    def save(self, *args, **kwargs):
        """Call clean before saving"""
        self.full_clean()
        if not self.item_number:
            last_item = Item.objects.all().order_by('id').last()
            next_number = 1001 if not last_item else last_item.id + 1001
            self.item_number = f'PART{next_number}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_number} - {self.name}"
    
    def get_tax_display(self):
        """Return formatted tax information"""
        taxes = []
        if self.gst and self.gst > 0:
            taxes.append(f"GST : {self.gst}%")
        if self.igst and self.igst > 0:
            taxes.append(f"IGST : {self.igst}%")
        return ", ".join(taxes) if taxes else "N/A"
    get_tax_display.short_description = "Tax"


# ---------- SNIPPET VIEWSETS ----------
class TypeViewSet(SnippetViewSet):
    model = Type
    icon = "cog"
    menu_label = "Types"


class MakeViewSet(SnippetViewSet):
    model = Make
    icon = "tag"
    menu_label = "Makes"


class UnitViewSet(SnippetViewSet):
    model = Unit
    icon = "form"
    menu_label = "Units"


class ItemViewSet(SnippetViewSet):
    model = Item
    icon = "clipboard-list"
    menu_label = "Items"
    inspect_view_enabled = True
    list_export = (
        'item_number', 'name', 'make', 'model', 'type', 'capacity',
        'threshold_qty', 'sale_price', 'purchase_price', 'service_type', 'tax_preference',
        'unit', 'sac_code', 'igst', 'gst'
    )
    list_display = (
        "item_number",
        "name",
        "type",
        "unit",
        "sale_price",
        "purchase_price",
        "tax_preference",
        "get_tax_display",
    )
    search_fields = (
        "item_number",
        "name",
        "make__value",
        "model",
        "type__value",
    )
    list_filter = (
        "make",
        "type",
        "unit",
    )

    def get_add_url(self):
        return reverse("add_item_custom")

    def get_edit_url(self, instance):
        return reverse("edit_item_custom", args=(instance.item_number,))

    def add_view(self, request):
        return redirect(self.get_add_url())

    def edit_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))


# ---------- GROUP ----------
class ItemGroup(SnippetViewSetGroup):
    items = (
        ItemViewSet,
        TypeViewSet,
        MakeViewSet,
        UnitViewSet
        
    )
    menu_icon = "clipboard-list" 
    menu_label = "Item "
    menu_name = "item"
    menu_order = 3


# ---------- REGISTER GROUP ----------
register_snippet(ItemGroup)