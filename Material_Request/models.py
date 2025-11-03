from django.db import models
from items.models import Item

class MaterialRequest(models.Model):
    date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    brand = models.CharField(max_length=200, blank=True)
    file = models.CharField(max_length=200)
    added_by = models.CharField(max_length=200)
    requested_by = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date']
