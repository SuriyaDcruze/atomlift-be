from customer.models import Customer
from complaints.models import Complaint
from amc.models import AMC
from invoice.models import Invoice
from PaymentReceived.models import PaymentReceived
from django.db.models import Sum


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
    }
