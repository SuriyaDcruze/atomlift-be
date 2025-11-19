import csv
import io
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.contrib import messages
from .models import PaymentReceived
from customer.models import Customer
from invoice.models import Invoice


def add_payment_received_custom(request):
    # Get customerId from URL parameter if provided
    customer_id = request.GET.get('customerId', None)
    preselected_customer = None
    if customer_id:
        try:
            preselected_customer = Customer.objects.get(id=customer_id)
        except (Customer.DoesNotExist, ValueError):
            pass
    
    return render(request, 'payments/add_payment_received_custom.html', {
        'is_edit': False,
        'preselected_customer': preselected_customer
    })


def edit_payment_received_custom(request, payment_number):
    payment = get_object_or_404(PaymentReceived, payment_number=payment_number)
    return render(request, 'payments/edit_payment_received_custom.html', {'is_edit': True, 'payment': payment})


@require_http_methods(["GET"])
def get_customers(request):
    data = [{
        'id': c.id,
        'site_name': c.site_name,
    } for c in Customer.objects.all().order_by('site_name')]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_invoices(request):
    data = [{
        'id': i.id,
        'number': getattr(i, 'reference_id', i.id),
        'customer_id': i.customer_id if hasattr(i, 'customer_id') else None,
    } for i in Invoice.objects.all().order_by('-id')]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_next_payment_number(request):
    last = PaymentReceived.objects.order_by('id').last()
    next_id = 1
    if last and last.payment_number and last.payment_number.startswith('PAY'):
        try:
            next_id = int(last.payment_number.replace('PAY', '')) + 1
        except ValueError:
            next_id = 1
    return JsonResponse({'payment_number': f'PAY{next_id:03d}'})


@csrf_exempt
@require_http_methods(["POST"])
def create_payment_received(request):
    import json as _json
    data = request.POST or {}
    if not data:
        try:
            data = _json.loads(request.body or '{}')
        except Exception:
            data = {}
    try:
        # Validate required fields
        if not data.get('customer'):
            return JsonResponse({
                'success': False,
                'error': 'Customer is required. Please select a customer.'
            }, status=400)
        
        amount = data.get('amount')
        if not amount or float(amount) <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Amount is required and must be greater than 0.'
            }, status=400)
        
        payment = PaymentReceived.objects.create(
            customer=Customer.objects.get(id=data['customer']),
            invoice=Invoice.objects.get(id=data['invoice']) if data.get('invoice') else None,
            amount=float(amount),
            date=data.get('date') or None,
            payment_type=data.get('payment_type') or 'cash',
            tax_deducted=data.get('tax_deducted') or 'no',
        )
        return JsonResponse({'success': True, 'message': f'Payment {payment.payment_number} created successfully'})
    except ValidationError as e:
        # Handle validation errors
        if e.message_dict:
            error_fields = ['customer', 'amount']
            for field in error_fields:
                if field in e.message_dict:
                    error_message = e.message_dict[field][0]
                    return JsonResponse({'success': False, 'error': error_message}, status=400)
            error_message = list(e.message_dict.values())[0][0]
        else:
            error_message = str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def update_payment_received(request, payment_number):
    import json as _json
    payment = get_object_or_404(PaymentReceived, payment_number=payment_number)
    data = request.POST or {}
    if not data:
        try:
            data = _json.loads(request.body or '{}')
        except Exception:
            data = {}
    try:
        # Validate required fields
        if not data.get('customer'):
            return JsonResponse({
                'success': False,
                'error': 'Customer is required. Please select a customer.'
            }, status=400)
        
        amount = data.get('amount')
        if not amount or float(amount) <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Amount is required and must be greater than 0.'
            }, status=400)
        
        payment.customer = Customer.objects.get(id=data['customer'])
        if data.get('invoice'):
            payment.invoice = Invoice.objects.get(id=data['invoice'])
        payment.amount = float(amount)
        if data.get('date'):
            payment.date = data.get('date')
        if data.get('payment_type'):
            payment.payment_type = data.get('payment_type')
        if data.get('tax_deducted'):
            payment.tax_deducted = data.get('tax_deducted')
        payment.save()
        return JsonResponse({'success': True, 'message': f'Payment {payment.payment_number} updated successfully'})
    except ValidationError as e:
        # Handle validation errors
        if e.message_dict:
            error_fields = ['customer', 'amount']
            for field in error_fields:
                if field in e.message_dict:
                    error_message = e.message_dict[field][0]
                    return JsonResponse({'success': False, 'error': error_message}, status=400)
            error_message = list(e.message_dict.values())[0][0]
        else:
            error_message = str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def bulk_import_view(request):
    """View for bulk importing payment received from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'payments/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'payments/bulk_import.html')
            
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
                    return render(request, 'payments/bulk_import.html')
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
                    return render(request, 'payments/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'payments/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'payments/bulk_import.html')
            
            # Process rows and create payments
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
                    
                    # Required fields (from create_payment_received requirements)
                    customer_value = row.get('customer', '') or row.get('customer_value', '') or ''
                    customer_value = str(customer_value).strip() if customer_value else ''
                    
                    amount_value = row.get('amount', '') or ''
                    amount_value = str(amount_value).strip() if amount_value else ''
                    
                    # Validate required fields (same as create_payment_received)
                    if not customer_value:
                        errors.append(f'Row {idx}: Customer is required.')
                        error_count += 1
                        continue
                    
                    if not amount_value:
                        errors.append(f'Row {idx}: Amount is required.')
                        error_count += 1
                        continue
                    
                    # Get customer by site_name
                    customer = Customer.objects.filter(site_name=customer_value).first()
                    if not customer:
                        errors.append(f'Row {idx}: Customer "{customer_value}" not found. Please use an existing customer site name.')
                        error_count += 1
                        continue
                    
                    # Validate and parse amount
                    try:
                        amount = float(amount_value)
                        if amount <= 0:
                            errors.append(f'Row {idx}: Amount must be greater than 0.')
                            error_count += 1
                            continue
                    except (ValueError, TypeError):
                        errors.append(f'Row {idx}: Amount must be a valid number.')
                        error_count += 1
                        continue
                    
                    # Optional fields
                    invoice_value = row.get('invoice', '') or row.get('invoice_value', '') or ''
                    invoice_value = str(invoice_value).strip() if invoice_value else ''
                    
                    invoice = None
                    if invoice_value:
                        invoice = Invoice.objects.filter(reference_id=invoice_value).first()
                        if not invoice:
                            errors.append(f'Row {idx}: Invoice "{invoice_value}" not found. Please use an existing invoice reference ID.')
                            error_count += 1
                            continue
                    
                    # Handle date (optional but recommended)
                    date_value = row.get('date', '') or row.get('date_str', '') or ''
                    date_parsed = None
                    if date_value:
                        date_parsed = parse_date(date_value)
                        if date_parsed is None:
                            errors.append(f'Row {idx}: Invalid date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    else:
                        # Date is required in the model, use today's date if not provided
                        from django.utils import timezone
                        date_parsed = timezone.now().date()
                    
                    # Payment type (optional, default: 'cash')
                    payment_type = row.get('payment_type', 'cash') or 'cash'
                    valid_payment_types = ['cash', 'bank_transfer', 'cheque', 'neft']
                    if payment_type not in valid_payment_types:
                        payment_type = 'cash'
                    
                    # Tax deducted (optional, default: 'no')
                    tax_deducted = row.get('tax_deducted', 'no') or 'no'
                    valid_tax_options = ['no', 'yes_tds']
                    if tax_deducted not in valid_tax_options:
                        tax_deducted = 'no'
                    
                    # Create payment (same structure as create_payment_received)
                    payment = PaymentReceived.objects.create(
                        customer=customer,
                        invoice=invoice,
                        amount=amount,
                        date=date_parsed,
                        payment_type=payment_type,
                        tax_deducted=tax_deducted,
                    )
                    
                    # Note: File uploads (uploads_files) cannot be handled in bulk import
                    # Users need to upload files individually after import
                    
                    # Validate and save (uses full_clean which applies all model validations)
                    try:
                        payment.full_clean()
                        payment.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors
                        if e.message_dict:
                            error_fields = ['customer', 'amount']
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
                messages.success(request, f'Successfully imported {success_count} payment(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if errors:
                    error_message += ' Errors: ' + '; '.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f' ... and {len(errors) - 10} more error(s).'
                messages.error(request, error_message)
            
            return render(request, 'payments/bulk_import.html')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return render(request, 'payments/bulk_import.html')
    
    # GET request - render form
    return render(request, 'payments/bulk_import.html')

