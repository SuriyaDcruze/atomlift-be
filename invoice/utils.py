from django.utils import timezone
from .models import Invoice

def update_overdue_invoices():
    """
    Updates the status of invoices to 'due' if the due_date has passed
    and the invoice is not paid (status is 'open' or 'partially_paid').
    """
    today = timezone.now().date()
    
    # Update invoices that are past due date and not paid
    updated_count = Invoice.objects.filter(
        due_date__lt=today,
        status__in=['open', 'partially_paid']
    ).update(status='due')
    
    return updated_count

