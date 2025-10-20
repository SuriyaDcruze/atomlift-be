from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum, Count
import json
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
    view_mode = request.GET.get('view')
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
    
    if view_mode == 'graph':
        by_status = complaints.values('priority').annotate(count=Count('id')).order_by()
        labels = [row['priority'] or 'Unknown' for row in by_status]
        data = [row['count'] for row in by_status]
        context = {
            'graph_title': 'Complaints by Status',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Count',
                    'data': data,
                    'backgroundColor': ['#60a5fa', '#34d399', '#fbbf24', '#a78bfa', '#f87171'][:len(data)],
                }
            ],
            'chart_type': 'bar',
        }
        return render(request, 'reports/graph_report.html', context)

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
    view_mode = request.GET.get('view')
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
    
    if view_mode == 'graph':
        by_status = invoices.values('status').annotate(count=Count('id')).order_by()
        labels = [row['status'] or 'Unknown' for row in by_status]
        data = [row['count'] for row in by_status]
        context = {
            'graph_title': 'Invoices by Status',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Count',
                    'data': data,
                    'backgroundColor': ['#60a5fa', '#34d399', '#fbbf24', '#a78bfa', '#f87171'][:len(data)],
                }
            ],
            'chart_type': 'doughnut',
        }
        return render(request, 'reports/graph_report.html', context)

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
    view_mode = request.GET.get('view')
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
    
    if view_mode == 'graph':
        # Aggregate by month and sum amount
        qs = payments
        # default to last 12 months if no range
        if not (start_date and end_date):
            twelve_months_ago = datetime.now() - timedelta(days=365)
            qs = qs.filter(date__gte=twelve_months_ago)
        totals = qs.values('date__year', 'date__month').annotate(total=Sum('amount')).order_by('date__year', 'date__month')
        labels = [f"{row['date__year']}-{str(row['date__month']).zfill(2)}" for row in totals]
        data = [float(row['total'] or 0) for row in totals]
        context = {
            'graph_title': 'Payments by Month (Total Amount)',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Amount',
                    'data': data,
                    'borderColor': '#10b981',
                    'backgroundColor': 'rgba(16,185,129,0.2)',
                    'fill': True,
                }
            ],
            'chart_type': 'line',
        }
        return render(request, 'reports/graph_report.html', context)

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
    view_mode = request.GET.get('view')
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
    
    if view_mode == 'graph':
        by_status = quotations.values('status').annotate(count=Count('id')).order_by()
        labels = [row['status'] or 'Unknown' for row in by_status]
        data = [row['count'] for row in by_status]
        context = {
            'graph_title': 'Quotations by Status',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Count',
                    'data': data,
                    'backgroundColor': ['#60a5fa', '#34d399', '#fbbf24', '#a78bfa', '#f87171'][:len(data)],
                }
            ],
            'chart_type': 'pie',
        }
        return render(request, 'reports/graph_report.html', context)

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
    view_mode = request.GET.get('view')
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
    
    if view_mode == 'graph':
        by_type = amc_records.values('amctype__amc_type_name').annotate(count=Count('id')).order_by()
        labels = [row['amctype__amc_type_name'] or 'Unknown' for row in by_type]
        data = [row['count'] for row in by_type]
        context = {
            'graph_title': 'Routine Services by AMC Type',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Count',
                    'data': data,
                    'backgroundColor': ['#60a5fa', '#34d399', '#fbbf24', '#a78bfa', '#f87171'][:len(data)],
                }
            ],
            'chart_type': 'bar',
        }
        return render(request, 'reports/graph_report.html', context)

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
def amc_report(request):
    """AMC Report View"""
    view_mode = request.GET.get('view')

    # Filters
    period = request.GET.get('period', 'ALL TIME')
    customer_filter = request.GET.get('customer', 'ALL')
    status_filter = request.GET.get('status', 'ALL')
    amc_type_filter = request.GET.get('amc_type', 'ALL')

    # Base queryset
    amcs = AMC.objects.all().select_related('customer', 'amc_type')

    # Apply period filter
    if period == 'CURRENT MONTH':
        amcs = amcs.filter(
            start_date__month=datetime.now().month,
            start_date__year=datetime.now().year
        )
    elif period == 'LAST 90 DAYS':
        amcs = amcs.filter(start_date__gte=datetime.now() - timedelta(days=90))

    # Apply other filters
    if customer_filter != 'ALL' and customer_filter:
        amcs = amcs.filter(customer__site_name=customer_filter)

    if status_filter != 'ALL' and status_filter:
        amcs = amcs.filter(status=status_filter)

    if amc_type_filter != 'ALL' and amc_type_filter:
        amcs = amcs.filter(amc_type__name=amc_type_filter)

    # Dropdown data
    customers = Customer.objects.all().values_list('site_name', flat=True).distinct()
    from amc.models import AMCType
    amc_types = AMCType.objects.all().values_list('name', flat=True)

    if view_mode == 'graph':
        # Graph per customer: stacked bar of Contract Amount, Total Paid, Amount Due
        per_customer_qs = amcs.values('customer__site_name').annotate(
            total_amount=Sum('contract_amount'),
            total_paid=Sum('total_amount_paid'),
            total_due=Sum('amount_due'),
        ).order_by('customer__site_name')

        # Pagination across customers (10 per page)
        page_size = 10
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        if page < 1:
            page = 1

        per_customer = list(per_customer_qs)
        total_count = len(per_customer)
        total_pages = (total_count + page_size - 1) // page_size if total_count else 1
        if page > total_pages:
            page = total_pages
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        current_rows = per_customer[start_index:end_index]

        labels = [row['customer__site_name'] or 'Unknown' for row in current_rows]
        dataset_amount = [float(row['total_amount'] or 0) for row in current_rows]
        dataset_paid = [float(row['total_paid'] or 0) for row in current_rows]
        dataset_due = [float(row['total_due'] or 0) for row in current_rows]

        datasets = [
            {
                'label': 'Contract Amount',
                'data': dataset_amount,
                'backgroundColor': '#60a5fa'
            },
            {
                'label': 'Total Paid',
                'data': dataset_paid,
                'backgroundColor': '#34d399'
            },
            {
                'label': 'Amount Due',
                'data': dataset_due,
                'backgroundColor': '#f87171'
            }
        ]

        # Build prev/next links preserving filters
        def build_url(target_page: int) -> str:
            query = request.GET.copy()
            query['view'] = 'graph'
            query['page'] = str(target_page)
            return f"{request.path}?{query.urlencode()}"

        has_prev = page > 1
        has_next = page < total_pages
        prev_url = build_url(page - 1) if has_prev else ''
        next_url = build_url(page + 1) if has_next else ''

        context = {
            'graph_title': 'AMC Financials by Customer',
            'labels_json': json.dumps(labels),
            'datasets_json': json.dumps(datasets),
            'chart_type': 'bar',
            'stacked': True,
            # pagination meta for template controls
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'start_index_display': (start_index + 1) if total_count else 0,
            'end_index_display': min(end_index, total_count),
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_url': prev_url,
            'next_url': next_url,
        }
        return render(request, 'reports/graph_report.html', context)

    context = {
        'amcs': amcs,
        'customers': customers,
        'amc_types': amc_types,
        'selected_period': period,
        'selected_customer': customer_filter,
        'selected_status': status_filter,
        'selected_amc_type': amc_type_filter,
    }
    return render(request, 'reports/amc_report.html', context)


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