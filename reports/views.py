from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum
from datetime import datetime, timedelta
import csv
import io
from complaints.models import Complaint
from invoice.models import Invoice
from PaymentReceived.models import PaymentReceived
from Quotation.models import Quotation
from amc.models import AMC
from customer.models import Customer


@login_required
def complaints_report(request):
    """Complaints Report View"""
    # Get filter parameters
    period = request.GET.get('period', 'ALL TIME')
    customer_filter = request.GET.get('customer', 'ALL')
    by_filter = request.GET.get('by', 'ALL')
    status_filter = request.GET.get('status', 'ALL')
    
    # Base queryset
    complaints = Complaint.objects.all().select_related('customer', 'assign_to')
    
    # Apply filters
    if period == 'LAST_WEEK':
        week_ago = datetime.now() - timedelta(days=7)
        complaints = complaints.filter(date__gte=week_ago)
    elif period == 'LAST_MONTH':
        month_ago = datetime.now() - timedelta(days=30)
        complaints = complaints.filter(date__gte=month_ago)
    
    if customer_filter != 'ALL':
        complaints = complaints.filter(customer__site_name=customer_filter)
    
    if status_filter != 'ALL':
        complaints = complaints.filter(priority=status_filter)
    
    # Get customer list for filter dropdown
    customers = Customer.objects.all().values_list('site_name', flat=True).distinct()
    
    context = {
        'complaints': complaints,
        'customers': customers,
        'selected_period': period,
        'selected_customer': customer_filter,
        'selected_by': by_filter,
        'selected_status': status_filter,
    }
    
    return render(request, 'reports/complaints_report.html', context)


@login_required
def invoice_report(request):
    """Invoice Report View"""
    # Get filter parameters
    period = request.GET.get('period', 'ALL TIME')
    customer_filter = request.GET.get('customer', 'ALL')
    by_filter = request.GET.get('by', 'ALL')
    status_filter = request.GET.get('status', 'ALL')
    
    # Base queryset
    invoices = Invoice.objects.all().select_related('customer')
    
    # Apply filters
    if period == 'CURRENT MONTH':
        invoices = invoices.filter(
            start_date__month=datetime.now().month,
            start_date__year=datetime.now().year
        )
    
    if customer_filter != 'ALL':
        invoices = invoices.filter(customer__site_name=customer_filter)
    
    if status_filter != 'ALL':
        invoices = invoices.filter(status=status_filter)
    
    # Get customer list for filter dropdown
    customers = Customer.objects.all().values_list('site_name', flat=True).distinct()
    
    context = {
        'invoices': invoices,
        'customers': customers,
        'selected_period': period,
        'selected_customer': customer_filter,
        'selected_by': by_filter,
        'selected_status': status_filter,
    }
    
    return render(request, 'reports/invoice_report.html', context)


@login_required
def payment_report(request):
    """Payment Report View"""
    # Get filter parameters
    customer_filter = request.GET.get('customer', '')
    status_filter = request.GET.get('status', 'ALL')
    payment_mode = request.GET.get('payment_mode', 'MONTH')
    period = request.GET.get('period', 'ALL')
    month = request.GET.get('month', datetime.now().strftime('%B'))
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Base queryset
    payments = PaymentReceived.objects.all().select_related('customer', 'invoice')
    
    # Apply filters
    if customer_filter:
        payments = payments.filter(customer__site_name=customer_filter)
    
    if start_date and end_date:
        payments = payments.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
        )
    
    # Get customer list for filter dropdown
    customers = Customer.objects.all().values_list('site_name', flat=True).distinct()
    
    context = {
        'payments': payments,
        'customers': customers,
        'selected_customer': customer_filter,
        'selected_status': status_filter,
        'selected_payment_mode': payment_mode,
        'selected_period': period,
        'selected_month': month,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/payment_report.html', context)


@login_required
def quotation_report(request):
    """Quotation Report View"""
    # Get filter parameters
    period = request.GET.get('period', 'ALL TIME')
    customer_filter = request.GET.get('customer', 'ALL')
    by_filter = request.GET.get('by', 'ALL')
    status_filter = request.GET.get('status', 'ALL')
    
    # Base queryset
    quotations = Quotation.objects.all().select_related('customer')
    
    # Apply filters
    if period == 'Today':
        quotations = quotations.filter(date=datetime.now().date())
    elif period == 'This Week':
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        quotations = quotations.filter(date__gte=week_start)
    elif period == 'This Month':
        quotations = quotations.filter(
            date__month=datetime.now().month,
            date__year=datetime.now().year
        )
    
    if customer_filter != 'ALL':
        quotations = quotations.filter(customer__site_name=customer_filter)
    
    if status_filter != 'ALL':
        quotations = quotations.filter(status=status_filter)
    
    # Get customer list for filter dropdown
    customers = Customer.objects.all().values_list('site_name', flat=True).distinct()
    
    context = {
        'quotations': quotations,
        'customers': customers,
        'selected_period': period,
        'selected_customer': customer_filter,
        'selected_by': by_filter,
        'selected_status': status_filter,
    }
    
    return render(request, 'reports/quotation_report.html', context)


@login_required
def routine_service_report(request):
    """Routine Service Report View"""
    # Get filter parameters
    customer_filter = request.GET.get('customer', '')
    by_filter = request.GET.get('by', 'DATE')
    status_filter = request.GET.get('status', 'ALL')
    amc_type_filter = request.GET.get('amc_types', '')
    period = request.GET.get('period', 'MONTH')
    month = request.GET.get('month', datetime.now().strftime('%B'))
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Base queryset
    amc_records = AMC.objects.all().select_related('customer', 'amctype')
    
    # Apply filters
    if customer_filter:
        amc_records = amc_records.filter(customer__site_name=customer_filter)
    
    if amc_type_filter:
        amc_records = amc_records.filter(amctype__amc_type_name=amc_type_filter)
    
    if status_filter != 'ALL':
        amc_records = amc_records.filter(status=status_filter)
    
    if start_date and end_date:
        amc_records = amc_records.filter(
            contract_start_date__gte=start_date,
            contract_start_date__lte=end_date
        )
    
    # Get customer list for filter dropdown
    customers = Customer.objects.all().values_list('site_name', flat=True).distinct()
    
    context = {
        'amc_records': amc_records,
        'customers': customers,
        'selected_customer': customer_filter,
        'selected_by': by_filter,
        'selected_status': status_filter,
        'selected_amc_type': amc_type_filter,
        'selected_period': period,
        'selected_month': month,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/routine_service_report.html', context)


@login_required
def export_complaints_csv(request):
    """Export Complaints to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Complaint No', 'Date', 'AMC ID', 'Site ID', 'Customer',
        'Type', 'Problem', 'Resolution', 'Done By', 'Status'
    ])
    
    complaints = Complaint.objects.all().select_related('customer', 'assign_to')
    for complaint in complaints:
        writer.writerow([
            complaint.reference or complaint.id,
            complaint.date.strftime('%d.%m.%Y') if complaint.date else '',
            complaint.amc_id or 'N/A',
            complaint.site_id or 'N/A',
            complaint.customer.site_name if complaint.customer else 'Unknown',
            complaint.complaint_type or 'General',
            complaint.subject or 'N/A',
            complaint.solution or 'Pending',
            complaint.assign_to.username if complaint.assign_to else 'Unassigned',
            complaint.priority or 'Open',
        ])
    
    return response


@login_required
def export_invoices_csv(request):
    """Export Invoices to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="invoice_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Invoice ID', 'Customer', 'Invoice Date', 'Due Date',
        'Value', 'Due Balance', 'Status'
    ])
    
    invoices = Invoice.objects.all().select_related('customer')
    for invoice in invoices:
        writer.writerow([
            invoice.reference_id or invoice.id,
            invoice.customer.site_name if invoice.customer else 'N/A',
            invoice.start_date,
            invoice.due_date,
            f'INR {invoice.value or 0.00}',
            f'INR {invoice.due_balance or 0.00}',
            invoice.status or 'Pending',
        ])
    
    return response


@login_required
def export_quotations_csv(request):
    """Export Quotations to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="quotation_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Number', 'Date', 'Name', 'AMC Details', 'Quotation Type',
        'Amount', 'GST', 'Net Amount', 'Status'
    ])
    
    quotations = Quotation.objects.all().select_related('customer')
    for quotation in quotations:
        writer.writerow([
            quotation.reference_id or quotation.id,
            quotation.date,
            quotation.customer.site_name if quotation.customer else 'N/A',
            quotation.amc_type or 'N/A',
            quotation.type or 'N/A',
            quotation.amount or 0,
            quotation.gst or '0%',
            quotation.net_amount or 0,
            quotation.status or 'Active',
        ])
    
    return response