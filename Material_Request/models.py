from django.db import models

class MaterialRequest(models.Model):
    date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    item = models.CharField(max_length=200)
    brand = models.CharField(max_length=200, blank=True)
    file = models.CharField(max_length=200)
    added_by = models.CharField(max_length=200)
    requested_by = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date']
