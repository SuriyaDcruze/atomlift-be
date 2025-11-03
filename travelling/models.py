from django.db import models
from django.conf import settings

class TravelRequest(models.Model):
    TRAVEL_MODES = [
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('flight', 'Flight'),
        ('car', 'Car'),
        ('taxi', 'Taxi'),
        ('other', 'Other'),
    ]

    travel_by = models.CharField(max_length=20, choices=TRAVEL_MODES, default='other')
    travel_date = models.DateField()
    from_place = models.CharField(max_length=100)
    to_place = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    attachment = models.FileField(upload_to='travel_attachments/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.created_by.username} - {self.from_place} to {self.to_place}"

    class Meta:
        ordering = ['-created_at']
