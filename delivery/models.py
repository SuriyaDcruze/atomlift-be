from django.db import models
from django.urls import reverse
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel


# ======================================================
#  SNIPPET MODELS
# ======================================================

class PlaceOfSupply(models.Model):
    value = models.CharField(max_length=100, unique=True)
    panels = [FieldPanel("value")]

    def __str__(self):
        return self.value


# ======================================================
#  MAIN MODEL
# ======================================================

class DeliveryChallan(ClusterableModel):
    REFERENCE_PREFIX = 'DC-'
    reference_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Customer Information
    customer = models.ForeignKey('customer.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    place_of_supply = models.ForeignKey(PlaceOfSupply, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Challan Details
    date = models.DateField()
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Challan Type
    CHALLAN_TYPE_CHOICES = [
        ('Supply of Liquid Gas', 'Supply of Liquid Gas'),
        ('Goods Supply', 'Goods Supply'),
        ('Service Delivery', 'Service Delivery'),
        ('Other', 'Other'),
    ]
    challan_type = models.CharField(
        max_length=50,
        choices=CHALLAN_TYPE_CHOICES,
        default='Supply of Liquid Gas'
    )
    
    # Financial Information
    currency = models.CharField(max_length=10, default='INR')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    adjustment = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Additional Information
    customer_note = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    uploads_files = models.FileField(upload_to='delivery_challan_uploads/', null=True, blank=True, max_length=100)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('reference_id', read_only=True),
            FieldPanel('customer'),
            FieldPanel('place_of_supply'),
            FieldPanel('date'),
            FieldPanel('challan_type'),
        ], heading="Challan Details"),
        
        MultiFieldPanel([
            FieldPanel('currency'),
            FieldPanel('discount_amount'),
            FieldPanel('discount_percentage'),
            FieldPanel('adjustment'),
        ], heading="Financial Information"),
        
        MultiFieldPanel([
            FieldPanel('customer_note'),
            FieldPanel('terms_conditions'),
            FieldPanel('uploads_files'),
        ], heading="Additional Information"),
        
        InlinePanel('items', label="Delivery Challan Items"),
    ]
    
    class Meta:
        verbose_name = "Delivery Challan"
        verbose_name_plural = "Delivery Challans"
        ordering = ['-date', '-id']
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            last_challan = DeliveryChallan.objects.all().order_by('id').last()
            if last_challan and last_challan.reference_id.startswith(self.REFERENCE_PREFIX):
                try:
                    # Extract number from "DC- 5" format
                    last_num = int(last_challan.reference_id.replace(self.REFERENCE_PREFIX, '').strip())
                    next_num = last_num + 1
                except (ValueError, AttributeError):
                    next_num = 1
            else:
                next_num = 1
            self.reference_id = f'{self.REFERENCE_PREFIX}{next_num}'
        super().save(*args, **kwargs)
    
    def get_subtotal(self):
        """Calculate subtotal from all items"""
        return sum(item.total for item in self.items.all())
    
    def get_total(self):
        """Calculate total after discount and adjustment"""
        subtotal = self.get_subtotal()
        
        # Apply discount
        if self.discount_percentage > 0:
            discount = subtotal * (self.discount_percentage / 100)
        else:
            discount = self.discount_amount
        
        total = subtotal - discount + self.adjustment
        return max(0, total)  # Ensure non-negative
    
    @property
    def subtotal(self):
        """Property for template compatibility"""
        return self.get_subtotal()
    
    @property
    def total(self):
        """Property for template compatibility"""
        return self.get_total()
    
    def __str__(self):
        return self.reference_id


class DeliveryChallanItem(models.Model):
    """Items in a delivery challan"""
    challan = ParentalKey(DeliveryChallan, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('items.Item', on_delete=models.SET_NULL, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    panels = [
        FieldPanel('item'),
        FieldPanel('rate'),
        FieldPanel('qty'),
        FieldPanel('tax'),
        FieldPanel('total', read_only=True),
    ]
    
    def save(self, *args, **kwargs):
        # Calculate total: (rate * qty) * (1 + tax/100)
        self.total = self.rate * self.qty * (1 + (self.tax / 100))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Item for {self.challan.reference_id}"


# ======================================================
#  WAGTAIL ADMIN VIEWSETS
# ======================================================

class PlaceOfSupplyViewSet(SnippetViewSet):
    model = PlaceOfSupply
    icon = "site"
    menu_label = "Places of Supply"


class DeliveryChallanViewSet(SnippetViewSet):
    model = DeliveryChallan
    icon = "doc-full"
    menu_label = "Delivery Challans"
    inspect_view_enabled = True
    
    list_display = ('reference_id', 'customer', 'date', 'challan_type', 'total')
    search_fields = ('reference_id', 'customer__site_name')
    list_filter = ('challan_type', 'date')
    
    list_export = [
        'reference_id', 'customer', 'date',
        'challan_type', 'place_of_supply', 'currency', 'total',
        'customer_note', 'terms_conditions'
    ]
    
    def get_add_url(self):
        return reverse("add_delivery_challan_custom")
    
    def get_edit_url(self, instance):
        return reverse("edit_delivery_challan_custom", args=(instance.reference_id,))
    
    def add_view(self, request):
        return redirect(self.get_add_url())
    
    def edit_view(self, request, pk):
        instance = self.model.objects.get(pk=pk)
        return redirect(self.get_edit_url(instance))


class DeliveryChallanGroup(SnippetViewSetGroup):
    items = (DeliveryChallanViewSet, PlaceOfSupplyViewSet)
    menu_icon = "doc-full"
    menu_label = "Delivery Challan"
    menu_name = "delivery_challan"
