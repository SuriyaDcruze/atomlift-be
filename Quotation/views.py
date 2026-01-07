import json
import csv
import io
import re
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import Quotation
from customer.models import Customer
from customer.utils import resolve_customer_from_email
from amc.models import AMCType
from authentication.models import CustomUser
from lift.models import Lift
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import logging
from .serializers import QuotationListSerializer

logger = logging.getLogger(__name__)


def sanitize_filename(name):
    """
    Sanitize a string to be safe for use in filenames.
    Removes or replaces special characters, spaces, etc.
    """
    if not name:
        return ''
    # Replace spaces and special characters with underscores
    # Keep only alphanumeric, underscores, and hyphens
    sanitized = re.sub(r'[^\w\s-]', '', str(name))
    # Replace spaces with underscores
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def _generate_quotation_pdf_buffer(quotation):
    """Helper function to generate PDF buffer for a quotation (used by download and email)"""
    # --- Context Preparation ---
    context = {
        'company_name': 'Atom Lifts India Pvt Ltd',
        'address': 'No.87B, Pillayar Koll Street, Mannurpet, Ambattur Indus Estate, Chennai 50',
        'phone': '9600087456',
        'email': 'admin@atomlifts.com',

        'quotation_no': quotation.reference_id,
        'quotation_date': quotation.date.strftime('%d/%m/%Y') if quotation.date else '',
        'customer_name': getattr(quotation.customer, 'site_name', '') if quotation.customer else '',
        'customer_address': getattr(quotation.customer, 'site_address', '') if quotation.customer else '',
        'amc_type': getattr(quotation.amc_type, 'name', '') if quotation.amc_type else '',
        'quotation_type': quotation.get_type_display() if quotation.type else '',
        'sales_executive': quotation.sales_service_executive.get_full_name() if quotation.sales_service_executive else '',
        'year_of_make': quotation.year_of_make or '',
        'remark': quotation.remark or '',
        'other_remark': quotation.other_remark or '',
    }

    # Get associated lifts
    lifts_list = list(quotation.lifts.all())

    # --- Build PDF ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle(name='HeaderStyle', parent=styles['Heading1'], fontSize=18, alignment=1)
    story.append(Paragraph(context['company_name'], header_style))
    story.append(Paragraph(context['address'], styles['Normal']))
    story.append(Paragraph(f"Phone: {context['phone']} | Email: {context['email']}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Quotation Summary
    data = [
        ['Quotation No:', context['quotation_no']],
        ['Quotation Date:', context['quotation_date']],
        ['Quotation Type:', context['quotation_type']],
        ['AMC Type:', context['amc_type']],
    ]
    summary_table = Table(data, colWidths=[120, 380])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Customer Info
    story.append(Paragraph("Customer Details", styles['Heading2']))
    cust_data = [
        ['Customer Name:', context['customer_name']],
        ['Address:', context['customer_address']],
        ['Sales/Service Executive:', context['sales_executive']],
    ]
    if context['year_of_make']:
        cust_data.append(['Year of Make:', context['year_of_make']])
    
    cust_table = Table(cust_data, colWidths=[140, 360])
    cust_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(cust_table)
    story.append(Spacer(1, 12))

    # Associated Lifts
    if lifts_list:
        story.append(Paragraph("Associated Lifts", styles['Heading2']))
        lifts_data = [['Lift Name', 'Reference ID']]
        for lift in lifts_list:
            lifts_data.append([
                lift.name or 'N/A',
                lift.reference_id or 'N/A',
            ])
        lifts_table = Table(lifts_data, colWidths=[250, 250])
        lifts_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(lifts_table)
        story.append(Spacer(1, 12))

    # Remarks
    if context['remark'] or context['other_remark']:
        story.append(Paragraph("Remarks", styles['Heading2']))
        if context['remark']:
            story.append(Paragraph(f"<b>Remark:</b> {context['remark']}", styles['Normal']))
            story.append(Spacer(1, 6))
        if context['other_remark']:
            story.append(Paragraph(f"<b>Other Remark:</b> {context['other_remark']}", styles['Normal']))
        story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer, context


def download_quotation_pdf(request, pk):
    """Generate and download a PDF for a specific quotation."""
    try:
        quotation = get_object_or_404(
            Quotation.objects.select_related('customer', 'amc_type', 'sales_service_executive').prefetch_related('lifts'),
            pk=pk
        )

        buffer, context = _generate_quotation_pdf_buffer(quotation)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        
        # Generate filename with customer name
        customer_name = sanitize_filename(context.get('customer_name', ''))
        quotation_no = context.get('quotation_no', '') or str(quotation.pk)
        
        if customer_name:
            filename = f'{customer_name}_quotation_{quotation_no}.pdf'
        else:
            filename = f'quotation_{quotation_no}.pdf'
        
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    except Exception as e:
        logger.error(f"Error generating quotation PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


def send_quotation_email(request, pk):
    """Send quotation PDF via email to customer"""
    from django.core.mail import EmailMessage
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        quotation = get_object_or_404(
            Quotation.objects.select_related('customer', 'amc_type', 'sales_service_executive').prefetch_related('lifts'),
            pk=pk
        )
        
        customer = quotation.customer
        if not customer or not customer.email:
            messages.error(request, 'Cannot send email: Customer has no email address.')
            return redirect('/admin/snippets/Quotation/quotation/')
        
        # Generate PDF
        buffer, context = _generate_quotation_pdf_buffer(quotation)
        
        # Generate filename
        customer_name = sanitize_filename(context.get('customer_name', ''))
        quotation_no = context.get('quotation_no', '') or str(quotation.pk)
        
        if customer_name:
            filename = f'{customer_name}_quotation_{quotation_no}.pdf'
        else:
            filename = f'quotation_{quotation_no}.pdf'
        
        # Build email
        subject = f'Quotation {quotation.reference_id} - Atom Lifts India Pvt Ltd'
        
        email_body = f"""Dear {customer.site_name or 'Valued Customer'},

Please find attached the quotation details.

Quotation Details:
- Quotation Number: {quotation.reference_id}
- Quotation Date: {context['quotation_date']}
- Quotation Type: {context['quotation_type']}
- AMC Type: {context['amc_type'] or 'N/A'}
- Sales/Service Executive: {context['sales_executive'] or 'N/A'}

Please review the attached quotation and contact us if you have any questions.

Thank you for your interest in our services.

Best regards,
Atom Lifts India Pvt Ltd
Phone: {context['phone']}
Email: {context['email']}
"""
        
        try:
            # Reset buffer position before reading
            buffer.seek(0)
            pdf_content = buffer.read()
            
            email = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=settings.EMAIL_HOST_USER,
                to=[customer.email],
            )
            email.attach(filename, pdf_content, 'application/pdf')
            email.send()
            
            logger.info(f"Quotation {quotation.reference_id} sent successfully to {customer.email}")
            messages.success(request, f'Quotation sent successfully to {customer.email}')
            
        except Exception as e:
            logger.error(f"Error sending quotation email for {quotation.reference_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Failed to send email: {str(e)}')
        
        return redirect('/admin/snippets/Quotation/quotation/')
        
    except Exception as e:
        logger.error(f"Error in send_quotation_email: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('/admin/snippets/Quotation/quotation/')


# quotation/views.py (relevant excerpts)
def add_quotation_custom(request):
    customer_id = request.GET.get('customer_id')
    preselected_customer = None
    if customer_id:
        try:
            preselected_customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            preselected_customer = None
    
    context = {
        'customers': Customer.objects.all().order_by('site_name'),
        'amc_types': AMCType.objects.all().order_by('name'),
        'users': CustomUser.objects.all().order_by('username'),
        'lifts': Lift.objects.all().order_by('name'),
        'is_edit': False,
        'selected_lift_ids': '',
        'preselected_customer_id': customer_id if preselected_customer else None,
        'preselected_customer': preselected_customer,
    }
    return render(request, 'quotation/add_quotation_custom.html', context)

def edit_quotation_custom(request, reference_id):
    quotation = get_object_or_404(Quotation, reference_id=reference_id)
    selected_lift_ids = ','.join(str(lift.id) for lift in quotation.lifts.all())
    context = {
        'quotation': quotation,
        'customers': Customer.objects.all().order_by('site_name'),
        'amc_types': AMCType.objects.all().order_by('name'),
        'users': CustomUser.objects.all().order_by('username'),
        'lifts': Lift.objects.all().order_by('name'),
        'is_edit': True,
        'selected_lift_ids': selected_lift_ids,
    }
    return render(request, 'quotation/edit_quotation_custom.html', context)
@csrf_exempt
@require_http_methods(["POST"])
def create_quotation(request):
    """Create a new quotation"""
    try:
        data = request.POST
        
        # Get customer
        customer_id = data.get('customer')
        if not customer_id:
            return JsonResponse({"success": False, "error": "Customer is required"}, status=400)
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get AMC type if provided
        amc_type = None
        if data.get('amc_type'):
            amc_type = get_object_or_404(AMCType, id=data.get('amc_type'))
        
        # Get sales/service executive if provided
        sales_service_executive = None
        if data.get('sales_service_executive'):
            sales_service_executive = get_object_or_404(CustomUser, id=data.get('sales_service_executive'))
        
        # Get year_of_make (handle empty string explicitly)
        year_of_make = data.get('year_of_make', '').strip() if data.get('year_of_make') else ''
        
        # Create quotation
        quotation = Quotation.objects.create(
            customer=customer,
            amc_type=amc_type,
            sales_service_executive=sales_service_executive,
            type=data.get('type', 'Parts/Peripheral Quotation'),
            year_of_make=year_of_make,
            remark=data.get('remark', ''),
            other_remark=data.get('other_remark', ''),
        )
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            quotation.uploads_files = request.FILES['uploads_files']
            quotation.save()
        
        # Handle date
        if data.get('date'):
            quotation.date = data.get('date')
            quotation.save()
        
        # Add selected lifts
        lift_ids = data.get('lifts', '').split(',')
        if lift_ids and lift_ids[0]:  # Check if not empty
            lifts = Lift.objects.filter(id__in=lift_ids)
            quotation.lifts.set(lifts)
        
        return JsonResponse({
            "success": True,
            "message": f"Quotation {quotation.reference_id} created successfully"
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_quotation(request, reference_id):
    """Update an existing quotation"""
    try:
        quotation = get_object_or_404(Quotation, reference_id=reference_id)
        data = request.POST
        
        # Update customer
        if data.get('customer'):
            customer = get_object_or_404(Customer, id=data.get('customer'))
            quotation.customer = customer
        
        # Update AMC type
        if data.get('amc_type'):
            amc_type = get_object_or_404(AMCType, id=data.get('amc_type'))
            quotation.amc_type = amc_type
        else:
            quotation.amc_type = None
        
        # Update sales/service executive
        if data.get('sales_service_executive'):
            sales_service_executive = get_object_or_404(CustomUser, id=data.get('sales_service_executive'))
            quotation.sales_service_executive = sales_service_executive
        else:
            quotation.sales_service_executive = None
        
        # Update other fields
        quotation.type = data.get('type', quotation.type)
        # Explicitly handle year_of_make - if it's in the form data (even if empty), use it
        if 'year_of_make' in data:
            quotation.year_of_make = data.get('year_of_make', '').strip() if data.get('year_of_make') else ''
        quotation.remark = data.get('remark', quotation.remark)
        quotation.other_remark = data.get('other_remark', quotation.other_remark)
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            quotation.uploads_files = request.FILES['uploads_files']
        
        # Handle date
        if data.get('date'):
            quotation.date = data.get('date')
        
        quotation.save()
        
        # Update selected lifts
        lift_ids = data.get('lifts', '').split(',')
        if lift_ids and lift_ids[0]:  # Check if not empty
            lifts = Lift.objects.filter(id__in=lift_ids)
            quotation.lifts.set(lifts)
        else:
            quotation.lifts.clear()
        
        return JsonResponse({
            "success": True,
            "message": f"Quotation {quotation.reference_id} updated successfully"
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# API endpoints for fetching dropdown options
@require_http_methods(["GET"])
@csrf_exempt
def get_customers(request):
    """Get all customers"""
    try:
        customers = Customer.objects.all().order_by('site_name')
        data = [
            {
                "id": customer.id, 
                "site_name": customer.site_name or "",
                "job_no": customer.job_no or "",
                "reference_id": customer.reference_id or "",
                "email": customer.email or "",
                "phone": customer.phone or ""
            }
            for customer in customers
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        import sys
        error_trace = ''.join(traceback.format_exception(*sys.exc_info()))
        print(f"Error in get_customers: {error_trace}", file=sys.stderr)
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_quotations(request):
    """Get existing quotations (minimal data for computing next reference id)"""
    try:
        quotations = Quotation.objects.all().only("reference_id").order_by("id")
        data = [
            {"reference_id": quotation.reference_id}
            for quotation in quotations
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_amc_types(request):
    """Get all AMC types"""
    try:
        amc_types = AMCType.objects.all().order_by('name')
        data = [
            {"id": amc_type.id, "name": amc_type.name}
            for amc_type in amc_types
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_executives(request):
    """Get all sales/service executives"""
    try:
        executives = CustomUser.objects.all().order_by('first_name', 'last_name', 'username')
        data = []
        for user in executives:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            data.append({"id": user.id, "username": user.username, "name": full_name})
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_lifts(request):
    """Get all lifts"""
    try:
        lifts = Lift.objects.all().order_by('name')
        data = [
            {
                "id": lift.id, 
                "name": lift.name,
                "reference_id": lift.reference_id,
                "brand": str(lift.brand) if lift.brand else "N/A"
            }
            for lift in lifts
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_lifts_by_customer(request):
    """Get lifts by customer ID (based on job_no matching lift_code)"""
    try:
        customer_id = request.GET.get('customer_id')
        if not customer_id:
            return JsonResponse({"error": "customer_id parameter is required"}, status=400)
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Fetch lifts where lift_code matches customer's job_no
        lifts = []
        if customer.job_no:
            lifts = Lift.objects.filter(lift_code=customer.job_no).order_by('name')
        
        data = [
            {
                "id": lift.id, 
                "name": lift.name,
                "reference_id": lift.reference_id,
                "lift_code": lift.lift_code or "",
                "brand": str(lift.brand) if lift.brand else "N/A"
            }
            for lift in lifts
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def bulk_import_view(request):
    """View for bulk importing quotations from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'quotation/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'quotation/bulk_import.html')
            
            # Read file content
            file_content = file.read()
            
            # Parse CSV
            if file_name.endswith('.csv'):
                try:
                    # Try to decode as UTF-8
                    try:
                        decoded_file = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try with different encoding
                        decoded_file = file_content.decode('latin-1')
                    
                    csv_reader = csv.DictReader(io.StringIO(decoded_file))
                    # Normalize headers to lowercase, strip whitespace, and replace spaces with underscores
                    rows = []
                    for row in csv_reader:
                        normalized_row = {}
                        for key, value in row.items():
                            # Normalize key: lowercase, strip, and replace spaces/hyphens with underscores
                            if key:
                                normalized_key = key.strip().lower().replace(' ', '_').replace('-', '_')
                            else:
                                normalized_key = ''
                            # Handle None values and convert to string
                            if value is None:
                                normalized_row[normalized_key] = ''
                            else:
                                normalized_row[normalized_key] = str(value) if value else ''
                        rows.append(normalized_row)
                except Exception as e:
                    messages.error(request, f'Error reading CSV file: {str(e)}')
                    return render(request, 'quotation/bulk_import.html')
            else:
                # Parse Excel file
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(io.BytesIO(file_content))
                    sheet = workbook.active
                    
                    # Get headers from first row, convert to lowercase, strip, and replace spaces with underscores
                    headers = []
                    for cell in sheet[1]:
                        header_value = cell.value
                        if header_value:
                            normalized_header = str(header_value).strip().lower().replace(' ', '_').replace('-', '_')
                            headers.append(normalized_header)
                        else:
                            headers.append('')
                    
                    rows = []
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        # Check if row has any non-empty values
                        if any(cell is not None and str(cell).strip() for cell in row if cell is not None):
                            # Create dict with lowercase keys and handle None values
                            row_dict = {}
                            for i, cell_value in enumerate(row):
                                if i < len(headers) and headers[i]:
                                    # Convert None to empty string, then to string
                                    if cell_value is None:
                                        row_dict[headers[i]] = ''
                                    else:
                                        # Handle datetime/date objects from Excel (convert to YYYY-MM-DD format)
                                        if isinstance(cell_value, (datetime, date)):
                                            row_dict[headers[i]] = cell_value.strftime('%Y-%m-%d')
                                        else:
                                            row_dict[headers[i]] = str(cell_value)
                            if row_dict:  # Only add if dict is not empty
                                rows.append(row_dict)
                except ImportError:
                    messages.error(request, 'openpyxl library is required for Excel files. Please install it: pip install openpyxl')
                    return render(request, 'quotation/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'quotation/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'quotation/bulk_import.html')
            
            # Process rows and create quotations
            success_count = 0
            error_count = 0
            errors = []
            
            # Helper function to parse dates in various formats
            def parse_date(date_str):
                """Parse date string in YYYY-MM-DD format or common Excel formats"""
                if not date_str or not date_str.strip():
                    return None
                date_str = date_str.strip()
                
                # Try YYYY-MM-DD format first (expected format)
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
                
                # Try other common formats
                date_formats = [
                    '%Y/%m/%d',
                    '%d/%m/%Y',
                    '%m/%d/%Y',
                    '%d-%m-%Y',
                    '%m-%d-%Y',
                ]
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
                
                # If all parsing fails, return None (will be caught by error handling)
                return None
            
            for idx, row in enumerate(rows, start=2):  # Start from 2 (1 is header)
                try:
                    # Map CSV columns to model fields - handle None values and empty strings
                    # Headers are normalized to lowercase with underscores
                    
                    # Required fields (from create_quotation requirements)
                    customer_value = row.get('customer', '') or row.get('customer_value', '') or ''
                    customer_value = str(customer_value).strip() if customer_value else ''
                    
                    # Validate required fields (same as create_quotation)
                    if not customer_value:
                        errors.append(f'Row {idx}: Customer is required.')
                        error_count += 1
                        continue
                    
                    # Get customer by site_name
                    customer = Customer.objects.filter(site_name=customer_value).first()
                    if not customer:
                        errors.append(f'Row {idx}: Customer "{customer_value}" not found. Please use an existing customer site name.')
                        error_count += 1
                        continue
                    
                    # Optional fields
                    amc_type_value = row.get('amc_type', '') or row.get('amc_type_value', '') or ''
                    amc_type_value = str(amc_type_value).strip() if amc_type_value else ''
                    
                    amc_type = None
                    if amc_type_value:
                        amc_type = AMCType.objects.filter(name=amc_type_value).first()
                        if not amc_type:
                            # Create if doesn't exist
                            amc_type = AMCType.objects.create(name=amc_type_value)
                    
                    sales_service_executive_value = row.get('sales_service_executive', '') or row.get('sales_service_executive_value', '') or ''
                    sales_service_executive_value = str(sales_service_executive_value).strip() if sales_service_executive_value else ''
                    
                    sales_service_executive = None
                    if sales_service_executive_value:
                        sales_service_executive = CustomUser.objects.filter(
                            username=sales_service_executive_value
                        ).first()
                        if not sales_service_executive:
                            errors.append(f'Row {idx}: Sales/Service Executive "{sales_service_executive_value}" not found.')
                            error_count += 1
                            continue
                    
                    # Text fields
                    quotation_type = row.get('type', 'Parts/Peripheral Quotation') or 'Parts/Peripheral Quotation'
                    if quotation_type not in [choice[0] for choice in Quotation.QUOTATION_TYPE_CHOICES]:
                        quotation_type = 'Parts/Peripheral Quotation'
                    
                    year_of_make = row.get('year_of_make', '') or ''
                    year_of_make = str(year_of_make).strip() if year_of_make else ''
                    
                    remark = row.get('remark', '') or ''
                    remark = str(remark).strip() if remark else ''
                    
                    other_remark = row.get('other_remark', '') or ''
                    other_remark = str(other_remark).strip() if other_remark else ''
                    
                    # Handle date (optional)
                    date_value = row.get('date', '') or row.get('date_str', '') or ''
                    date_parsed = None
                    if date_value:
                        date_parsed = parse_date(date_value)
                        if date_parsed is None:
                            errors.append(f'Row {idx}: Invalid date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    
                    # Handle lifts (comma-separated lift codes or names)
                    lifts_str = row.get('lifts', '') or row.get('lifts_str', '') or ''
                    lifts = []
                    if lifts_str:
                        lift_values = [v.strip() for v in str(lifts_str).split(',') if v.strip()]
                        for lift_value in lift_values:
                            # Try to find by lift_code first, then by name
                            lift = Lift.objects.filter(lift_code=lift_value).first()
                            if not lift:
                                lift = Lift.objects.filter(name=lift_value).first()
                            if lift:
                                lifts.append(lift)
                            else:
                                # Don't fail, just warn
                                errors.append(f'Row {idx}: Lift "{lift_value}" not found. Skipping this lift.')
                    
                    # Create quotation (same structure as create_quotation)
                    quotation = Quotation.objects.create(
                        customer=customer,
                        amc_type=amc_type,
                        sales_service_executive=sales_service_executive,
                        type=quotation_type,
                        year_of_make=year_of_make,
                        remark=remark,
                        other_remark=other_remark,
                    )
                    
                    # Set date if provided
                    if date_parsed:
                        quotation.date = date_parsed
                        quotation.save()
                    
                    # Add lifts if provided
                    if lifts:
                        quotation.lifts.set(lifts)
                    
                    # Note: File uploads (uploads_files) cannot be handled in bulk import
                    # Users need to upload files individually after import
                    
                    # Validate and save (uses full_clean which applies all model validations)
                    try:
                        quotation.full_clean()
                        quotation.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors
                        if e.message_dict:
                            error_fields = ['customer']
                            error_msg = None
                            for field in error_fields:
                                if field in e.message_dict:
                                    error_msg = f"Row {idx}: {e.message_dict[field][0]}"
                                    break
                            if not error_msg:
                                error_msg = f"Row {idx}: {list(e.message_dict.values())[0][0]}"
                        else:
                            error_msg = f"Row {idx}: {str(e)}"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    except Exception as e:
                        # Handle unique constraint violations and other database errors
                        error_str = str(e).lower()
                        if 'unique' in error_str or 'duplicate' in error_str or 'already exists' in error_str:
                            errors.append(f'Row {idx}: Duplicate entry - {str(e)}')
                        else:
                            errors.append(f'Row {idx}: {str(e)}')
                        error_count += 1
                        continue
                        
                except Exception as e:
                    errors.append(f'Row {idx}: Unexpected error - {str(e)}')
                    error_count += 1
                    continue
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} quotation(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if errors:
                    error_message += ' Errors: ' + '; '.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f' ... and {len(errors) - 10} more error(s).'
                messages.error(request, error_message)
            
            return render(request, 'quotation/bulk_import.html')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return render(request, 'quotation/bulk_import.html')
    
    # GET request - render form
    return render(request, 'quotation/bulk_import.html')


# ======================================================
#  CUSTOMER MOBILE APP QUOTATION APIs
# ======================================================

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def customer_quotations_list(request):
    """
    Get all quotations for a specific customer by email
    Only customers can view their own quotations
    """
    email = request.query_params.get('email')
    
    if not email:
        return Response(
            {'error': 'Email parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Find customer by email (also checks for sub-customers)
        customer, is_subcustomer = resolve_customer_from_email(email)
        
        # Get all quotations for this customer
        quotations = Quotation.objects.filter(
            customer=customer
        ).select_related('customer', 'amc_type', 'sales_service_executive').prefetch_related('lifts').order_by('-date')
        
        # Serialize quotations
        serializer = QuotationListSerializer(quotations, many=True)
        
        response_data = {
            'quotations': serializer.data,
            'count': quotations.count(),
            'message': 'Quotations retrieved successfully'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found with this email address'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error retrieving customer quotations: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )