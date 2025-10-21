from django.db import models
from django.conf import settings
from customer.models import Customer
from items.models import Item

class RoutineService(models.Model):
    """Model for routine services/maintenance schedules"""

    SERVICE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='routine_services')
    lift = models.ForeignKey('lift.Lift', on_delete=models.CASCADE, related_name='routine_services')
    service_date = models.DateField()
    service_type = models.CharField(max_length=100, help_text="Type of routine service")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=SERVICE_STATUS_CHOICES, default='pending')
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.customer.name} - {self.service_type} ({self.service_date})"

    def is_overdue(self):
        """Check if service is overdue"""
        from django.utils import timezone
        return self.service_date < timezone.now().date() and self.status not in ['completed', 'cancelled']
