from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList


class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('earned', 'Earned Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    half_day = models.BooleanField(default=False)
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"

    # Admin panels for Wagtail
    panels = [
        MultiFieldPanel([
            FieldPanel("user"),
            FieldPanel("email"),
        ], heading="User Information"),
        
        MultiFieldPanel([
            FieldPanel("leave_type"),
            FieldPanel("half_day"),
            FieldPanel("from_date"),
            FieldPanel("to_date"),
        ], heading="Leave Details"),
        
        MultiFieldPanel([
            FieldPanel("reason"),
            FieldPanel("status"),
            FieldPanel("admin_remarks"),
        ], heading="Status & Remarks"),
    ]
    
    edit_handler = TabbedInterface([
        ObjectList(panels, heading="Leave Request Details"),
    ])

    def __str__(self):
        return f"{self.user} - {self.leave_type} ({self.status})"


# Store old status before saving for signal use
_old_status_cache = {}

@receiver(models.signals.pre_save, sender=LeaveRequest)
def leave_request_pre_save(sender, instance, **kwargs):
    """Store old status before saving"""
    if instance.pk:
        try:
            old_instance = LeaveRequest.objects.get(pk=instance.pk)
            _old_status_cache[instance.pk] = old_instance.status
        except LeaveRequest.DoesNotExist:
            pass


@receiver(post_save, sender=LeaveRequest)
def send_leave_status_email_signal(sender, instance, created, **kwargs):
    """
    Send email notification when leave request status is approved or rejected.
    This works for both API updates and Wagtail admin updates.
    """
    # Only process if this is an update (not a new creation)
    if created:
        return
    
    # Check if status was changed to approved or rejected
    try:
        if instance.pk and instance.pk in _old_status_cache:
            old_status = _old_status_cache.pop(instance.pk)
            
            # Check if status actually changed and is now approved/rejected
            if old_status != instance.status and instance.status in ['approved', 'rejected']:
                # Import here to avoid circular imports
                from .views import send_leave_status_email
                send_leave_status_email(instance, old_status, instance.status)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in leave status email signal: {e}", exc_info=True)
