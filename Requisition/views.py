import csv
import io
from datetime import datetime, date
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.views.decorators.http import require_http_methods
from .models import Requisition, StockRegister
from items.models import Item
from customer.models import Customer
from amc.models import AMC
from authentication.models import CustomUser

def add_requisition_custom(request):
    """Custom add requisition page"""
    items = Item.objects.all()
    customers = Customer.objects.all()
    amcs = AMC.objects.all()
    employees = CustomUser.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('site'):
                return JsonResponse({'success': False, 'error': 'Customer is required'})
            if not data.get('date'):
                return JsonResponse({'success': False, 'error': 'Date is required'})
            if not data.get('item'):
                return JsonResponse({'success': False, 'error': 'Item is required'})
            if not data.get('qty') or int(data.get('qty', 0)) < 1:
                return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'})
            if not data.get('amc_id'):
                return JsonResponse({'success': False, 'error': 'AMC is required'})
            if not data.get('employee'):
                return JsonResponse({'success': False, 'error': 'Employee is required'})
            
            # Get foreign key objects
            item = get_object_or_404(Item, id=data['item'])
            site = get_object_or_404(Customer, id=data['site'])
            amc = get_object_or_404(AMC, id=data['amc_id'])
            employee = get_object_or_404(CustomUser, id=data['employee'])
            
            # Create new requisition
            requisition = Requisition.objects.create(
                reference_id=data.get('reference_id'),  # Set reference_id from form
                date=data.get('date'),
                item=item,
                qty=data.get('qty', 0),
                site=site,
                amc_id=amc,
                service=data.get('service', ''),
                employee=employee,
                status=data.get('status', 'OPEN'),
                approve_for=data.get('approve_for', 'PENDING')
            )
            return JsonResponse({'success': True, 'message': 'Requisition created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'requisition/add_requisition_custom.html', {
        'items': items,
        'customers': customers,
        'amcs': amcs,
        'employees': employees,
        'is_edit': False
    })

def edit_requisition_custom(request, reference_id):
    """Custom edit requisition page"""
    try:
        requisition = Requisition.objects.get(reference_id=reference_id)
    except Requisition.DoesNotExist:
        messages.error(request, 'Requisition not found')
        return render(request, '404.html')

    items = Item.objects.all()
    customers = Customer.objects.all()
    amcs = AMC.objects.all()
    employees = CustomUser.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('site'):
                return JsonResponse({'success': False, 'error': 'Customer is required'})
            if not data.get('date'):
                return JsonResponse({'success': False, 'error': 'Date is required'})
            if not data.get('item'):
                return JsonResponse({'success': False, 'error': 'Item is required'})
            if not data.get('qty') or int(data.get('qty', 0)) < 1:
                return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'})
            if not data.get('amc_id'):
                return JsonResponse({'success': False, 'error': 'AMC is required'})
            if not data.get('employee'):
                return JsonResponse({'success': False, 'error': 'Employee is required'})
            
            # Get foreign key objects
            item = get_object_or_404(Item, id=data['item'])
            site = get_object_or_404(Customer, id=data['site'])
            amc = get_object_or_404(AMC, id=data['amc_id'])
            employee = get_object_or_404(CustomUser, id=data['employee'])
            
            # Update requisition
            requisition.date = data.get('date')
            requisition.item = item
            requisition.qty = data.get('qty', 0)
            requisition.site = site
            requisition.amc_id = amc
            requisition.service = data.get('service', '')
            requisition.employee = employee
            requisition.status = data.get('status', 'OPEN')
            requisition.approve_for = data.get('approve_for', 'PENDING')
            requisition.save()

            return JsonResponse({'success': True, 'message': 'Requisition updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'requisition/add_requisition_custom.html', {
        'requisition': requisition,
        'items': items,
        'customers': customers,
        'amcs': amcs,
        'employees': employees,
        'is_edit': True
    })


@require_http_methods(["GET"])
def get_next_requisition_reference(request):
    """Return the next Requisition reference ID e.g., REQ001, REQ002"""
    try:
        last_requisition = Requisition.objects.order_by("id").last()
        last_id = 0
        if last_requisition and last_requisition.reference_id and last_requisition.reference_id.startswith("REQ"):
            try:
                last_id = int(last_requisition.reference_id.replace("REQ", ""))
            except ValueError:
                last_id = 0
        next_ref = f"REQ{str(last_id + 1).zfill(3)}"
        return JsonResponse({"reference_id": next_ref})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_customers(request):
    """Get all customers for requisition"""
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
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_users(request):
    """Get all users for requisition employee field"""
    try:
        users = CustomUser.objects.all().order_by('first_name', 'last_name', 'username')
        data = []
        for user in users:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            data.append({
                "id": user.id,
                "name": full_name,
                "username": user.username,
                "email": user.email or "",
                "full_name": full_name
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_next_stock_register_reference(request):
    """Return the next Stock Register number (predicted) e.g., STK0001"""
    try:
        last_entry = StockRegister.objects.all().order_by('id').last()
        if last_entry and last_entry.register_no.startswith('STK'):
            last_id = int(last_entry.register_no.replace('STK', ''))
            next_ref = f'STK{str(last_id + 1).zfill(4)}'
        else:
            next_ref = 'STK0001'
        return JsonResponse({"register_no": next_ref})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def add_stock_register_custom(request):
    """Custom add stock register page"""
    items = Item.objects.all()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('date'):
                return JsonResponse({'success': False, 'error': 'Date is required'})
            if not data.get('item'):
                return JsonResponse({'success': False, 'error': 'Item is required'})
            if not data.get('transaction_type'):
                return JsonResponse({'success': False, 'error': 'Transaction type is required'})
            
            # Get foreign key objects
            item = get_object_or_404(Item, id=data['item'])
            
            # Validate quantity based on transaction type
            if data['transaction_type'] == 'INWARD':
                if not data.get('inward_qty') or int(data.get('inward_qty', 0)) < 1:
                    return JsonResponse({'success': False, 'error': 'Inward quantity must be at least 1'})
                outward_qty = 0
                inward_qty = int(data.get('inward_qty', 0))
            else:  # OUTWARD
                if not data.get('outward_qty') or int(data.get('outward_qty', 0)) < 1:
                    return JsonResponse({'success': False, 'error': 'Outward quantity must be at least 1'})
                inward_qty = 0
                outward_qty = int(data.get('outward_qty', 0))
            
            # Validate unit value
            unit_value = float(data.get('unit_value', 0))
            if unit_value < 0:
                return JsonResponse({'success': False, 'error': 'Unit value cannot be negative'})
            
            # Create new stock register entry
            stock_register = StockRegister.objects.create(
                date=data.get('date'),
                item=item,
                description=data.get('description', ''),
                transaction_type=data['transaction_type'],
                inward_qty=inward_qty,
                outward_qty=outward_qty,
                unit_value=unit_value,
                reference=data.get('reference', '')
            )
            return JsonResponse({'success': True, 'message': 'Stock Register entry created successfully', 'register_no': stock_register.register_no})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'requisition/add_stock_register_custom.html', {
        'items': items,
        'is_edit': False
    })


@login_required
def edit_stock_register_custom(request, register_no):
    """Custom edit stock register page"""
    try:
        stock_register = StockRegister.objects.get(register_no=register_no)
    except StockRegister.DoesNotExist:
        messages.error(request, 'Stock Register entry not found')
        return render(request, '404.html')
    
    items = Item.objects.all()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('date'):
                return JsonResponse({'success': False, 'error': 'Date is required'})
            if not data.get('item'):
                return JsonResponse({'success': False, 'error': 'Item is required'})
            if not data.get('transaction_type'):
                return JsonResponse({'success': False, 'error': 'Transaction type is required'})
            
            # Get foreign key objects
            item = get_object_or_404(Item, id=data['item'])
            
            # Validate quantity based on transaction type
            if data['transaction_type'] == 'INWARD':
                if not data.get('inward_qty') or int(data.get('inward_qty', 0)) < 1:
                    return JsonResponse({'success': False, 'error': 'Inward quantity must be at least 1'})
                outward_qty = 0
                inward_qty = int(data.get('inward_qty', 0))
            else:  # OUTWARD
                if not data.get('outward_qty') or int(data.get('outward_qty', 0)) < 1:
                    return JsonResponse({'success': False, 'error': 'Outward quantity must be at least 1'})
                inward_qty = 0
                outward_qty = int(data.get('outward_qty', 0))
            
            # Validate unit value
            unit_value = float(data.get('unit_value', 0))
            if unit_value < 0:
                return JsonResponse({'success': False, 'error': 'Unit value cannot be negative'})
            
            # Update stock register entry
            stock_register.date = data.get('date')
            stock_register.item = item
            stock_register.description = data.get('description', '')
            stock_register.transaction_type = data['transaction_type']
            stock_register.inward_qty = inward_qty
            stock_register.outward_qty = outward_qty
            stock_register.unit_value = unit_value
            stock_register.reference = data.get('reference', '')
            stock_register.save()
            
            return JsonResponse({'success': True, 'message': 'Stock Register entry updated successfully', 'register_no': stock_register.register_no})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'requisition/add_stock_register_custom.html', {
        'stock_register': stock_register,
        'items': items,
        'is_edit': True
    })


def bulk_import_view(request):
    """View for bulk importing requisitions from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'requisition/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'requisition/bulk_import.html')
            
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
                    return render(request, 'requisition/bulk_import.html')
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
                    return render(request, 'requisition/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'requisition/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'requisition/bulk_import.html')
            
            # Process rows and create requisitions
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
                    
                    # Required fields (from add_requisition_custom requirements)
                    site_value = row.get('site', '') or row.get('site_value', '') or row.get('customer', '') or ''
                    site_value = str(site_value).strip() if site_value else ''
                    
                    date_value = row.get('date', '') or row.get('date_str', '')
                    
                    item_value = row.get('item', '') or row.get('item_value', '') or ''
                    item_value = str(item_value).strip() if item_value else ''
                    
                    qty_value = row.get('qty', '') or row.get('quantity', '')
                    
                    amc_id_value = row.get('amc_id', '') or row.get('amc_id_value', '') or row.get('amc', '') or ''
                    amc_id_value = str(amc_id_value).strip() if amc_id_value else ''
                    
                    employee_value = row.get('employee', '') or row.get('employee_value', '') or ''
                    employee_value = str(employee_value).strip() if employee_value else ''
                    
                    # Validate required fields (same as add_requisition_custom)
                    if not site_value:
                        errors.append(f'Row {idx}: Customer (Site) is required.')
                        error_count += 1
                        continue
                    
                    if not date_value:
                        errors.append(f'Row {idx}: Date is required.')
                        error_count += 1
                        continue
                    
                    if not item_value:
                        errors.append(f'Row {idx}: Item is required.')
                        error_count += 1
                        continue
                    
                    if not qty_value or int(qty_value) < 1:
                        errors.append(f'Row {idx}: Quantity must be at least 1.')
                        error_count += 1
                        continue
                    
                    if not amc_id_value:
                        errors.append(f'Row {idx}: AMC is required.')
                        error_count += 1
                        continue
                    
                    if not employee_value:
                        errors.append(f'Row {idx}: Employee is required.')
                        error_count += 1
                        continue
                    
                    # Get foreign key objects
                    site = Customer.objects.filter(site_name=site_value).first()
                    if not site:
                        errors.append(f'Row {idx}: Customer "{site_value}" not found. Please use an existing customer site name.')
                        error_count += 1
                        continue
                    
                    date_parsed = parse_date(date_value)
                    if date_parsed is None:
                        errors.append(f'Row {idx}: Invalid date format. Please use YYYY-MM-DD format.')
                        error_count += 1
                        continue
                    
                    item = Item.objects.filter(name=item_value).first()
                    if not item:
                        errors.append(f'Row {idx}: Item "{item_value}" not found. Please use an existing item name.')
                        error_count += 1
                        continue
                    
                    qty = int(qty_value)
                    if qty < 1:
                        errors.append(f'Row {idx}: Quantity must be at least 1.')
                        error_count += 1
                        continue
                    
                    # Get AMC - try by reference_id or id
                    amc = None
                    try:
                        # Try as integer ID first
                        amc_id_int = int(amc_id_value)
                        amc = AMC.objects.filter(id=amc_id_int).first()
                    except (ValueError, TypeError):
                        pass
                    
                    if not amc:
                        # Try by reference_id or other string identifier
                        amc = AMC.objects.filter(reference_id=amc_id_value).first()
                    
                    if not amc:
                        errors.append(f'Row {idx}: AMC "{amc_id_value}" not found. Please use an existing AMC ID or reference ID.')
                        error_count += 1
                        continue
                    
                    # Get employee by username
                    employee = CustomUser.objects.filter(username=employee_value).first()
                    if not employee:
                        errors.append(f'Row {idx}: User "{employee_value}" not found. Please use an existing username.')
                        error_count += 1
                        continue
                    
                    # Optional fields
                    service = row.get('service', '').strip() if row.get('service') else ''
                    status = row.get('status', 'OPEN') or 'OPEN'
                    valid_statuses = ['OPEN', 'CLOSED']
                    if status not in valid_statuses:
                        status = 'OPEN'
                    
                    approve_for = row.get('approve_for', 'PENDING') or 'PENDING'
                    valid_approve_for = ['PENDING', 'APPROVED', 'REJECTED']
                    if approve_for not in valid_approve_for:
                        approve_for = 'PENDING'
                    
                    # Create requisition (same structure as add_requisition_custom)
                    requisition = Requisition.objects.create(
                        date=date_parsed,
                        item=item,
                        qty=qty,
                        site=site,
                        amc_id=amc,
                        service=service,
                        employee=employee,
                        status=status,
                        approve_for=approve_for
                    )
                    
                    # Validate and save (uses full_clean which applies all model validations)
                    try:
                        requisition.full_clean()
                        requisition.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors
                        if e.message_dict:
                            error_fields = ['site', 'date', 'item', 'qty', 'amc_id', 'employee']
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
                messages.success(request, f'Successfully imported {success_count} requisition(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if errors:
                    error_message += ' Errors: ' + '; '.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f' ... and {len(errors) - 10} more error(s).'
                messages.error(request, error_message)
            
            return render(request, 'requisition/bulk_import.html')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return render(request, 'requisition/bulk_import.html')
    
    # GET request - render form
    return render(request, 'requisition/bulk_import.html')
