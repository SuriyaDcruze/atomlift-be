# invoice/views.py
import csv
import io
from datetime import datetime, date
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ValidationError
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging
import json

from .models import Invoice, InvoiceItem

logger = logging.getLogger(__name__)


def download_invoice_pdf(request, pk):
    """Generate and download a PDF for a specific invoice."""
    try:
        invoice = get_object_or_404(
            Invoice.objects.select_related('customer', 'amc_type').prefetch_related('items__item'),
            pk=pk
        )

        # --- Context Preparation ---
        context = {
            'company_name': 'Atom Lifts India Pvt Ltd',
            'address': 'No.87B, Pillayar Koll Street, Mannurpet, Ambattur Indus Estate, Chennai 50',
            'phone': '9600087456',
            'email': 'admin@atomlifts.com',

            'invoice_no': invoice.reference_id,
            'invoice_date': invoice.start_date.strftime('%d/%m/%Y') if invoice.start_date else '',
            'due_date': invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else '',
            'customer_name': getattr(invoice.customer, 'site_name', '') if invoice.customer else '',
            'customer_address': getattr(invoice.customer, 'site_address', '') if invoice.customer else '',
            'amc_type': getattr(invoice.amc_type, 'name', '') if invoice.amc_type else '',
            'discount': f"{invoice.discount}%",
            'payment_term': invoice.get_payment_term_display(),
            'status': invoice.get_status_display(),
        }

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

        # Invoice Summary
        data = [
            ['Invoice No:', context['invoice_no']],
            ['Invoice Date:', context['invoice_date']],
            ['Due Date:', context['due_date']],
            ['AMC Type:', context['amc_type']],
            ['Status:', context['status']],
        ]
        summary_table = Table(data, colWidths=[100, 400])
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
            ['Payment Term:', context['payment_term']],
            ['Discount:', context['discount']],
        ]
        cust_table = Table(cust_data, colWidths=[100, 400])
        cust_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(cust_table)
        story.append(Spacer(1, 12))

        # Invoice Items
        story.append(Paragraph("Invoice Items", styles['Heading2']))
        item_data = [['Item', 'Rate', 'Qty', 'Tax (%)', 'Total']]
        for item in invoice.items.all():
            item_data.append([
                getattr(item.item, 'name', 'N/A'),
                f"{item.rate:.2f}",
                str(item.qty),
                f"{item.tax:.2f}",
                f"{item.total:.2f}",
            ])
        item_table = Table(item_data, colWidths=[180, 80, 60, 80, 100])
        item_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 12))

        # Totals
        grand_total = sum(item.total for item in invoice.items.all())
        story.append(Paragraph(f"<b>Grand Total:</b> ₹{grand_total:.2f}", styles['Heading3']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=invoice_{context["invoice_no"]}.pdf'
        return response

    except Exception as e:
        logger.error(f"Error generating invoice PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


@csrf_exempt
def add_invoice_custom(request):
    from customer.models import Customer
    from amc.models import AMCType
    from items.models import Item
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validate required fields
            if not data.get('amc_type'):
                return JsonResponse({'success': False, 'error': 'AMC Type is required'}, status=400)

            invoice = Invoice.objects.create(
                customer_id=data.get('customer') or None,
                amc_type_id=data.get('amc_type'),
                start_date=data.get('start_date'),
                due_date=data.get('due_date'),
                discount=data.get('discount', 0),
                payment_term=data.get('payment_term', 'cash'),
                status=data.get('status', 'open'),
            )

            # ✅ Save invoice items correctly
            for item_data in data.get('items', []):
                if not item_data.get('item'):
                    continue
                InvoiceItem.objects.create(
                    invoice=invoice,
                    item_id=item_data.get('item'),
                    rate=item_data.get('rate', 0),
                    qty=item_data.get('qty', 1),
                    tax=item_data.get('tax', 0),
                )

            return JsonResponse({'success': True, 'message': 'Invoice created successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # GET: render form
    customers = Customer.objects.all()
    amc_types = AMCType.objects.all()
    items = Item.objects.all()
    
    # Get customerId from URL parameter if provided
    customer_id = request.GET.get('customerId', None)
    preselected_customer = None
    if customer_id:
        try:
            preselected_customer = Customer.objects.get(id=customer_id)
        except (Customer.DoesNotExist, ValueError):
            pass

    # Generate preview invoice number for new invoices
    preview_invoice_number = None
    if not request.GET.get('edit'):
        last_invoice = Invoice.objects.all().order_by('id').last()
        if last_invoice and last_invoice.reference_id.startswith(Invoice.REFERENCE_PREFIX):
            last_id = int(last_invoice.reference_id.replace(Invoice.REFERENCE_PREFIX, ''))
        else:
            last_id = 0
        preview_invoice_number = f'{Invoice.REFERENCE_PREFIX}{str(last_id + 1).zfill(3)}'

    return render(request, 'invoice/add_invoice_custom.html', {
        'customers': customers,
        'amc_types': amc_types,
        'items': items,
        'is_edit': False,
        'preselected_customer': preselected_customer,
        'preview_invoice_number': preview_invoice_number
    })


def view_invoice_custom(request, reference_id):
    """Custom invoice detail view"""
    try:
        invoice = Invoice.objects.select_related('customer', 'amc_type').prefetch_related('items__item').get(reference_id=reference_id)
    except Invoice.DoesNotExist:
        messages.error(request, 'Invoice not found')
        return render(request, '404.html')
    
    return render(request, 'invoice/view_invoice_custom.html', {
        'invoice': invoice,
    })


def edit_invoice_custom(request, reference_id):
    """Custom edit invoice page"""
    from customer.models import Customer
    from amc.models import AMCType
    from items.models import Item
    
    try:
        invoice = Invoice.objects.select_related('customer', 'amc_type').prefetch_related('items__item').get(reference_id=reference_id)
    except Invoice.DoesNotExist:
        messages.error(request, 'Invoice not found')
        return render(request, '404.html')

    customers = Customer.objects.all()
    amc_types = AMCType.objects.all()
    items = Item.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validate required fields
            if not data.get('amc_type'):
                return JsonResponse({'success': False, 'error': 'AMC Type is required'}, status=400)

            # Update invoice fields
            invoice.customer_id = data.get('customer') if data.get('customer') else None
            invoice.amc_type_id = data.get('amc_type')
            invoice.start_date = data.get('start_date')
            invoice.due_date = data.get('due_date')
            invoice.discount = data.get('discount', 0)
            invoice.payment_term = data.get('payment_term', 'cash')
            invoice.status = data.get('status', 'open')
            if data.get('uploads_files'):
                invoice.uploads_files = data.get('uploads_files')
            invoice.save()

            # Handle invoice items
            # First, delete existing items
            invoice.items.all().delete()
            
            # Then create new items
            for item_data in data.get('items', []):
                if not item_data.get('item'):
                    continue
                InvoiceItem.objects.create(
                    invoice=invoice,
                    item_id=item_data.get('item'),
                    rate=item_data.get('rate', 0),
                    qty=item_data.get('qty', 1),
                    tax=item_data.get('tax', 0),
                )

            return JsonResponse({'success': True, 'message': 'Invoice updated successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'invoice/add_invoice_custom.html', {
        'invoice': invoice,
        'customers': customers,
        'amc_types': amc_types,
        'items': items,
        'is_edit': True
    })


# API endpoints for dropdown management
@csrf_exempt
def manage_customers(request):
    """API for managing customers: GET list, POST create"""
    from customer.models import Customer
    
    if request.method == 'GET':
        customers = Customer.objects.all().values('id', 'site_name').order_by('site_name')
        return JsonResponse(list(customers), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            site_name = data.get('site_name', '').strip()
            if not site_name:
                return JsonResponse({"error": "Site name is required"}, status=400)
            if Customer.objects.filter(site_name=site_name).exists():
                return JsonResponse({"error": "Customer already exists"}, status=400)
            customer = Customer.objects.create(site_name=site_name)
            return JsonResponse({
                "success": True,
                "id": customer.id,
                "site_name": customer.site_name
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def manage_amc_types(request):
    """API for managing AMC types: GET list, POST create"""
    from amc.models import AMCType
    
    if request.method == 'GET':
        amc_types = AMCType.objects.all().values('id', 'name').order_by('name')
        return JsonResponse(list(amc_types), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)
            if AMCType.objects.filter(name=name).exists():
                return JsonResponse({"error": "AMC Type already exists"}, status=400)
            amc_type = AMCType.objects.create(name=name)
            return JsonResponse({
                "success": True,
                "id": amc_type.id,
                "name": amc_type.name
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def manage_customers_detail(request, pk):
    """API for updating/deleting customers"""
    from customer.models import Customer
    
    try:
        customer = Customer.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            site_name = data.get('site_name', '').strip()
            if not site_name:
                return JsonResponse({"error": "Site name is required"}, status=400)
            if Customer.objects.filter(site_name=site_name).exclude(pk=pk).exists():
                return JsonResponse({"error": "Customer already exists"}, status=400)
            customer.site_name = site_name
            customer.save()
            return JsonResponse({'success': True, 'message': 'Customer updated'})
        elif request.method == 'DELETE':
            customer.delete()
            return JsonResponse({'success': True, 'message': 'Customer deleted'})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def manage_amc_types_detail(request, pk):
    """API for updating/deleting AMC types"""
    from amc.models import AMCType
    
    try:
        amc_type = AMCType.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)
            if AMCType.objects.filter(name=name).exclude(pk=pk).exists():
                return JsonResponse({"error": "AMC Type already exists"}, status=400)
            amc_type.name = name
            amc_type.save()
            return JsonResponse({'success': True, 'message': 'AMC Type updated'})
        elif request.method == 'DELETE':
            amc_type.delete()
            return JsonResponse({'success': True, 'message': 'AMC Type deleted'})
    except AMCType.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'AMC Type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def manage_items(request):
    """API for managing items: GET list"""
    from items.models import Item
    
    if request.method == 'GET':
        items = Item.objects.all().values('id', 'name', 'sale_price').order_by('name')
        return JsonResponse(list(items), safe=False)


def bulk_import_view(request):
    """View for bulk importing invoices from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'invoice/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'invoice/bulk_import.html')
            
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
                    return render(request, 'invoice/bulk_import.html')
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
                    return render(request, 'invoice/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'invoice/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'invoice/bulk_import.html')
            
            # Process rows and create invoices
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
                    
                    # Required fields (from add_invoice_custom requirements)
                    amc_type_value = row.get('amc_type', '') or row.get('amc_type_value', '') or ''
                    amc_type_value = str(amc_type_value).strip() if amc_type_value else ''
                    
                    # Validate required fields (same as add_invoice_custom)
                    if not amc_type_value:
                        errors.append(f'Row {idx}: AMC Type is required.')
                        error_count += 1
                        continue
                    
                    # Get AMC type by name
                    from amc.models import AMCType
                    amc_type = AMCType.objects.filter(name=amc_type_value).first()
                    if not amc_type:
                        errors.append(f'Row {idx}: AMC Type "{amc_type_value}" not found. Please use an existing AMC type name.')
                        error_count += 1
                        continue
                    
                    # Optional fields
                    customer_value = row.get('customer', '') or row.get('customer_value', '') or ''
                    customer_value = str(customer_value).strip() if customer_value else ''
                    
                    customer = None
                    if customer_value:
                        from customer.models import Customer
                        customer = Customer.objects.filter(site_name=customer_value).first()
                        if not customer:
                            errors.append(f'Row {idx}: Customer "{customer_value}" not found. Please use an existing customer site name.')
                            error_count += 1
                            continue
                    
                    # Handle dates (required in model)
                    start_date_value = row.get('start_date', '') or row.get('start_date_str', '') or ''
                    start_date_parsed = None
                    if start_date_value:
                        start_date_parsed = parse_date(start_date_value)
                        if start_date_parsed is None:
                            errors.append(f'Row {idx}: Invalid start date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    else:
                        # Use today's date if not provided
                        from django.utils import timezone
                        start_date_parsed = timezone.now().date()
                    
                    due_date_value = row.get('due_date', '') or row.get('due_date_str', '') or ''
                    due_date_parsed = None
                    if due_date_value:
                        due_date_parsed = parse_date(due_date_value)
                        if due_date_parsed is None:
                            errors.append(f'Row {idx}: Invalid due date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    else:
                        # Use start_date + 30 days if not provided
                        from datetime import timedelta
                        due_date_parsed = start_date_parsed + timedelta(days=30)
                    
                    # Validate date order
                    if start_date_parsed >= due_date_parsed:
                        errors.append(f'Row {idx}: Start date must be before due date.')
                        error_count += 1
                        continue
                    
                    # Parse numeric fields
                    discount = 0.00
                    discount_value = row.get('discount', '0') or '0'
                    try:
                        discount = float(discount_value)
                        if discount < 0:
                            discount = 0.00
                    except (ValueError, TypeError):
                        discount = 0.00
                    
                    # Payment term (optional, default: 'cash')
                    payment_term = row.get('payment_term', 'cash') or 'cash'
                    valid_payment_terms = ['cash', 'cheque', 'neft']
                    if payment_term not in valid_payment_terms:
                        payment_term = 'cash'
                    
                    # Status (optional, default: 'open')
                    status = row.get('status', 'open') or 'open'
                    valid_statuses = ['open', 'paid', 'partially_paid']
                    if status not in valid_statuses:
                        status = 'open'
                    
                    # Handle invoice items (optional - JSON format or comma-separated)
                    items_data = []
                    items_str = row.get('items', '') or ''
                    if items_str:
                        try:
                            # Try to parse as JSON first
                            items_data = json.loads(items_str)
                            if not isinstance(items_data, list):
                                items_data = []
                        except (json.JSONDecodeError, ValueError):
                            # If not JSON, try comma-separated format: "item_name:rate:qty:tax,item_name2:rate2:qty2:tax2"
                            items_list = [item.strip() for item in str(items_str).split(',') if item.strip()]
                            for item_str in items_list:
                                parts = item_str.split(':')
                                if len(parts) >= 2:
                                    item_name = parts[0].strip()
                                    rate = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                                    qty = int(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else 1
                                    tax = float(parts[3].strip()) if len(parts) > 3 and parts[3].strip() else 0
                                    items_data.append({
                                        'item': item_name,
                                        'rate': rate,
                                        'qty': qty,
                                        'tax': tax
                                    })
                    
                    # Create invoice (same structure as add_invoice_custom)
                    invoice = Invoice.objects.create(
                        customer=customer,
                        amc_type=amc_type,
                        start_date=start_date_parsed,
                        due_date=due_date_parsed,
                        discount=discount,
                        payment_term=payment_term,
                        status=status,
                    )
                    
                    # Add invoice items if provided
                    if items_data:
                        from items.models import Item
                        for item_data in items_data:
                            # Handle both dict format (from JSON) and simplified format
                            if isinstance(item_data, dict):
                                item_name = item_data.get('item') or item_data.get('item_name', '')
                                item_obj = None
                                if item_name:
                                    item_obj = Item.objects.filter(name=item_name).first()
                                    if not item_obj:
                                        errors.append(f'Row {idx}: Item "{item_name}" not found. Skipping this item.')
                                        continue
                                
                                rate = float(item_data.get('rate', 0))
                                qty = int(item_data.get('qty', 1))
                                tax = float(item_data.get('tax', 0))
                                
                                if item_obj:
                                    InvoiceItem.objects.create(
                                        invoice=invoice,
                                        item=item_obj,
                                        rate=rate,
                                        qty=qty,
                                        tax=tax,
                                    )
                    
                    # Note: File uploads (uploads_files) cannot be handled in bulk import
                    # Users need to upload files individually after import
                    
                    # Validate and save (uses full_clean which applies all model validations)
                    try:
                        invoice.full_clean()
                        invoice.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors
                        if e.message_dict:
                            error_fields = ['amc_type', 'start_date', 'due_date']
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
                messages.success(request, f'Successfully imported {success_count} invoice(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if errors:
                    error_message += ' Errors: ' + '; '.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f' ... and {len(errors) - 10} more error(s).'
                messages.error(request, error_message)
            
            return render(request, 'invoice/bulk_import.html')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return render(request, 'invoice/bulk_import.html')
    
    # GET request - render form
    return render(request, 'invoice/bulk_import.html')
