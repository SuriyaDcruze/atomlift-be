from django.db import models

# Create your models here.

class MonthlyLoad(models.Model):
    """Model for monthly load management"""

    class Meta:
        verbose_name = "Monthly Load"
        verbose_name_plural = "Monthly Loads"

    def __str__(self):
        return f"Monthly Load {self.id}"
