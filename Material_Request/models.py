from django.db import models
from items.models import Item

class MaterialRequest(models.Model):
    date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    brand = models.CharField(max_length=200, blank=True)
    file = models.CharField(max_length=200, blank=True)
    added_by = models.CharField(max_length=200)
    requested_by = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date']


# Proxy model for Bulk Import menu item (not used for actual data)
class BulkImportMaterialRequest(MaterialRequest):
    """Proxy model used only for menu structure - redirects to bulk import view"""
    class Meta:
        proxy = True
        verbose_name = "Bulk Import"
        verbose_name_plural = "Bulk Import"