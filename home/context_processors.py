from customer.models import Customer
from complaints.models import Complaint
from amc.models import AMC
from invoice.models import Invoice
from PaymentReceived.models import PaymentReceived
from Routine_services.models import RoutineService
from employeeleave.models import LeaveRequest
from Material_Request.models import MaterialRequest
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.utils import timezone


def dashboard_metrics(request):
    """
    Context processor to add dashboard metrics to admin templates.
    """
    from datetime import timedelta
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

    # Weekly payment received data for the graph - using PaymentReceived model
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())  # Start of current week (Monday)
    week_end = week_start + timedelta(days=6)  # End of current week (Sunday)
    
    weekly_payments = []
    weekly_services = []
    
    # Get payment received data for each day of the week from PaymentReceived model
    for i in range(7):
        day = week_start + timedelta(days=i)
        # Sum all PaymentReceived amounts for this specific day
        # Filter by date field and exclude any NULL dates
        day_payments = PaymentReceived.objects.filter(
            date=day
        ).exclude(date__isnull=True).aggregate(total=Sum('amount'))['total'] or 0
        
        # Convert Decimal to float for chart display
        payment_amount = float(day_payments) if day_payments else 0.0
        weekly_payments.append(payment_amount)
        
        # Count completed services for each day
        day_services = RoutineService.objects.filter(
            service_date=day,
            status='completed'
        ).count()
        weekly_services.append(day_services)

    # ----------------- Invoice notifications (due soon / overdue) -----------------
    # unpaid invoices: open / partially_paid / due
    unpaid_statuses = ['open', 'partially_paid', 'due']
    # Due soon: within next 3 days (including today), not overdue
    upcoming_window = today + timedelta(days=3)
    due_soon_qs = Invoice.objects.select_related('customer').filter(
        status__in=unpaid_statuses,
        due_date__gte=today,
        due_date__lte=upcoming_window,
    ).order_by('due_date')

    # Overdue: due_date < today
    overdue_qs = Invoice.objects.select_related('customer').filter(
        status__in=unpaid_statuses,
        due_date__lt=today,
    ).order_by('due_date')

    # Limit lists for dashboard dropdown
    due_soon_list = list(due_soon_qs[:10])
    overdue_list = list(overdue_qs[:10])
    invoice_notification_count = due_soon_qs.count() + overdue_qs.count()

    # ----------------- AMC expiry notifications -----------------
    # Only show AMCs going to expire (due soon), not expired ones
    amc_qs_base = AMC.objects.select_related('customer').filter(end_date__isnull=False, end_date__gte=today)
    amc_due_7_qs = amc_qs_base.filter(end_date__lte=today + timedelta(days=7)).order_by('end_date')
    amc_due_30_qs = amc_qs_base.filter(end_date__gt=today + timedelta(days=7), end_date__lte=today + timedelta(days=30)).order_by('end_date')

    amc_due_7_list = list(amc_due_7_qs[:10])
    amc_due_30_list = list(amc_due_30_qs[:10])
    amc_notification_count = amc_due_7_qs.count() + amc_due_30_qs.count()

    # ----------------- Leave Request notifications -----------------
    # Get pending leave requests from technicians (users in employee groups)
    pending_leave_qs = LeaveRequest.objects.select_related('user').filter(
        status='pending'
    ).filter(
        user__groups__isnull=False
    ).distinct().order_by('-created_at')
    
    pending_leave_list = list(pending_leave_qs[:10])
    leave_notification_count = pending_leave_qs.count()

    # ----------------- Material Request notifications -----------------
    # Get recent material requests (from last 7 days, or all if less than 10)
    # Since MaterialRequest doesn't have status, show recent requests that need attention
    recent_material_qs = MaterialRequest.objects.select_related('item').filter(
        date__gte=today - timedelta(days=7)
    ).order_by('-date')
    
    # If we have less than 10 in the last 7 days, get the 10 most recent overall
    material_count = recent_material_qs.count()
    if material_count < 10:
        recent_material_qs = MaterialRequest.objects.select_related('item').order_by('-date')
        material_count = recent_material_qs.count()
    
    recent_material_list = list(recent_material_qs[:10])
    material_notification_count = material_count

    notification_count_total = invoice_notification_count + amc_notification_count + leave_notification_count + material_notification_count

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
        # Notifications
        'invoice_due_soon_list': due_soon_list,
        'invoice_overdue_list': overdue_list,
        'invoice_notification_count': invoice_notification_count,
        # AMC notifications (only expiring soon, not expired)
        'amc_due_7_list': amc_due_7_list,
        'amc_due_30_list': amc_due_30_list,
        'amc_notification_count': amc_notification_count,
        # Leave request notifications
        'pending_leave_list': pending_leave_list,
        'leave_notification_count': leave_notification_count,
        # Material request notifications
        'recent_material_list': recent_material_list,
        'material_notification_count': material_notification_count,
        # Total badge
        'notification_count_total': notification_count_total,
    }
