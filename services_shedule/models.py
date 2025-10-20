from django.db import models

# Create your models here.

class ServiceSchedule(models.Model):
    """Model for service schedule management"""

    class Meta:
        verbose_name = "Service Schedule"
        verbose_name_plural = "Service Schedules"

    def __str__(self):
        return f"Service Schedule {self.id}"
