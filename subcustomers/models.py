from django.db import models
from django.utils import timezone
from customer.models import Customer


class SubCustomer(models.Model):
    """
    Model for sub-customers that belong to a customer.
    Sub-customers can access the customer's user app if can_access_app is True.
    """
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='subcustomers',
        help_text="The parent customer who owns this sub-customer"
    )
    name = models.CharField(max_length=200, help_text="Full name of the sub-customer")
    email = models.EmailField(help_text="Email address of the sub-customer")
    phone = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number of the sub-customer")
    can_access_app = models.BooleanField(
        default=False,
        help_text="If checked, this sub-customer can access the user app with the customer's credentials"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this sub-customer is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Email of the customer who created this sub-customer"
    )

    class Meta:
        verbose_name = "Sub Customer"
        verbose_name_plural = "Sub Customers"
        ordering = ['-created_at']
        # Ensure unique email per customer
        unique_together = [['customer', 'email']]

    def __str__(self):
        return f"{self.name} ({self.customer.site_name})"

    def save(self, *args, **kwargs):
        """Override save to validate email uniqueness within customer"""
        super().save(*args, **kwargs)
