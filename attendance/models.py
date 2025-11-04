from django.db import models
from django.conf import settings
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList


class AttendanceRecord(models.Model):
    """
    Model to store employee attendance records with check-in and check-out details
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    
    # Check-in details
    check_in_time = models.DateTimeField(null=True, blank=True, verbose_name='Check-In Time')
    check_in_date = models.DateField(null=True, blank=True, verbose_name='Check-In Date')
    check_in_selfie = models.ImageField(
        upload_to='attendance/selfies/',
        null=True,
        blank=True,
        verbose_name='Check-In Selfie'
    )
    check_in_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Check-In Location'
    )
    check_in_note = models.TextField(
        blank=True,
        null=True,
        verbose_name='Check-In Note'
    )
    
    # Check-out details
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name='Check-Out Time')
    check_out_date = models.DateField(null=True, blank=True, verbose_name='Check-Out Date')
    check_out_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Check-Out Location'
    )
    check_out_note = models.TextField(
        blank=True,
        null=True,
        verbose_name='Check-Out Note'
    )
    
    # Status tracking
    is_checked_in = models.BooleanField(default=False, verbose_name='Is Checked In')
    is_checked_out = models.BooleanField(default=False, verbose_name='Is Checked Out')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-check_in_date', '-check_in_time']
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = [['user', 'check_in_date']]  # One record per user per day
    
    # Admin panels for Wagtail
    panels = [
        MultiFieldPanel([
            FieldPanel("user"),
        ], heading="User Information"),
        
        MultiFieldPanel([
            FieldPanel("check_in_time"),
            FieldPanel("check_in_date"),
            FieldPanel("check_in_selfie"),
            FieldPanel("check_in_location"),
            FieldPanel("check_in_note"),
            FieldPanel("is_checked_in"),
        ], heading="Check-In Details"),
        
        MultiFieldPanel([
            FieldPanel("check_out_time"),
            FieldPanel("check_out_date"),
            FieldPanel("check_out_location"),
            FieldPanel("check_out_note"),
            FieldPanel("is_checked_out"),
        ], heading="Check-Out Details"),
    ]
    
    edit_handler = TabbedInterface([
        ObjectList(panels, heading="Attendance Details"),
    ])
    
    def __str__(self):
        check_in_str = self.check_in_time.strftime('%Y-%m-%d %H:%M') if self.check_in_time else 'N/A'
        check_out_str = self.check_out_time.strftime('%Y-%m-%d %H:%M') if self.check_out_time else 'N/A'
        return f"{self.user.get_full_name()} - {check_in_str} / {check_out_str}"
    
    def calculate_work_duration(self):
        """Calculate work duration in hours if both check-in and check-out are available"""
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            return round(duration.total_seconds() / 3600, 2)  # Convert to hours
        return None
    
    def get_work_duration_display(self):
        """Get work duration as formatted string"""
        duration = self.calculate_work_duration()
        if duration is not None:
            hours = int(duration)
            minutes = int((duration - hours) * 60)
            return f"{hours}h {minutes}m"
        return "N/A"


