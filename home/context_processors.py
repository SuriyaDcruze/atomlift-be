from customer.models import Customer
from complaints.models import Complaint
from amc.models import AMC
from invoice.models import Invoice
from PaymentReceived.models import PaymentReceived
from Routine_services.models import RoutineService
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.utils import timezone


def dashboard_metrics(request):
    """
    Context processor to add dashboard metrics to admin templates.
    """
    total_customers = Customer.objects.count()
    total_complaints = Complaint.objects.count()
    # Count complaints where status is 'open' or 'in_progress' (not 'closed')
    open_complaints = Complaint.objects.filter(status__in=['open', 'in_progress']).count()
    total_amc_due = AMC.objects.filter(status='active').aggregate(total=Sum('amount_due'))['total'] or 0
    # Assuming Income is sum of contract_amount paid or total payments
    total_income = PaymentReceived.objects.aggregate(total=Sum('amount'))['total'] or 0
    # Open Invoices: invoices that are not paid
    total_invoices = Invoice.objects.count()
    open_invoices = Invoice.objects.filter(status__in=['open', 'partially_paid']).count()

    # Recent complaints for dashboard table
    recent_complaints = Complaint.objects.select_related('assign_to').order_by('-created')[:5]

    # Weekly payment received data for the graph
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())  # Start of current week (Monday)
    
    weekly_payments = []
    weekly_services = []  # We'll keep services data for now, but you can modify this
    
    # Get payment data for each day of the week
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_payments = PaymentReceived.objects.filter(date=day).aggregate(total=Sum('amount'))['total'] or 0
        
        # Convert to float for chart display
        payment_amount = float(day_payments)
        weekly_payments.append(payment_amount)
        
        # Count completed services for each day
        day_services = RoutineService.objects.filter(
            service_date=day,
            status='completed'
        ).count()
        weekly_services.append(day_services)

    return {
        'total_customers': total_customers,
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'amc_due_count': AMC.objects.filter(amount_due__gt=0).count(),
        'amc_due_total': total_amc_due,
        'total_income': total_income,
        'open_invoices': open_invoices,
        'total_invoices': total_invoices,
        'recent_complaints': recent_complaints,
        'weekly_payments': weekly_payments,
        'weekly_services': weekly_services,
    }
