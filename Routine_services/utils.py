from django.utils import timezone
from .models import RoutineService

def update_overdue_routine_services():
    """
    Updates the status of routine services to 'overdue' if the service date has passed
    and the status is still 'pending' or 'due'.
    """
    today = timezone.now().date()
    
    # Update RoutineService (uses 'pending')
    RoutineService.objects.filter(
        service_date__lt=today,
        status='pending'
    ).update(status='overdue')
    
    # Update AMCRoutineService if available (uses 'due')
    try:
        from amc.models import AMCRoutineService
        AMCRoutineService.objects.filter(
            service_date__lt=today,
            status='due'
        ).update(status='overdue')
    except ImportError:
        pass
