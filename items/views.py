# views.py (corrected to handle POST in list APIs, consolidated CRUD, added error checking like in lifts, renamed detail functions)
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Item, Type, Make, Unit
import json
import csv
import io

def add_item_custom(request):
    """Custom add item page"""
    types = Type.objects.all()
    makes = Make.objects.all()
    units = Unit.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Validate make is provided
            make_id = data.get('make')
            if not make_id:
                return JsonResponse({'success': False, 'error': 'Make is required. Please select a make.'})
            
            # Create new item
            item = Item(
                name=data.get('name'),
                make_id=make_id,
                model=data.get('model'),
                type_id=data.get('type') if data.get('type') else None,
                capacity=data.get('capacity'),
                threshold_qty=data.get('threshold_qty') if data.get('threshold_qty') is not None else None,
                sale_price=data.get('sale_price', 0),
                purchase_price=data.get('purchase_price') if data.get('purchase_price') is not None else None,
                service_type=data.get('service_type', 'Goods'),
                tax_preference=data.get('tax_preference', 'Non-Taxable'),
                unit_id=data.get('unit') if data.get('unit') else None,
                sac_code=data.get('sac_code', '').strip() if data.get('sac_code') else None,
                igst=data.get('igst', 0),
                gst=data.get('gst', 0),
                description=data.get('description', '')
            )
            item.full_clean()
            item.save()
            return JsonResponse({'success': True, 'message': 'Item created successfully'})
        except ValidationError as e:
            # Handle validation errors for multiple fields
            if e.message_dict:
                # Prioritize showing field-specific errors
                error_fields = ['name', 'make', 'capacity', 'sale_price', 'sac_code']
                for field in error_fields:
                    if field in e.message_dict:
                        error_message = e.message_dict[field][0]
                        return JsonResponse({'success': False, 'error': error_message})
                # Fallback to first error if none of the prioritized fields have errors
                error_message = list(e.message_dict.values())[0][0]
            else:
                error_message = str(e)
            return JsonResponse({'success': False, 'error': error_message})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Calculate next item number to display
    last_item = Item.objects.all().order_by('id').last()
    next_number = 1001 if not last_item else last_item.id + 1001
    next_item_number = f'PART{next_number}'

    return render(request, 'items/add_item_custom.html', {
        'types': types,
        'makes': makes,
        'units': units,
        'is_edit': False,
        'next_item_number': next_item_number
    })

def edit_item_custom(request, item_number):
    """Custom edit item page"""
    try:
        item = Item.objects.get(item_number=item_number)
    except Item.DoesNotExist:
        messages.error(request, 'Item not found')
        return render(request, '404.html')

    types = Type.objects.all()
    makes = Make.objects.all()
    units = Unit.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Validate make is provided
            make_id = data.get('make')
            if not make_id:
                return JsonResponse({'success': False, 'error': 'Make is required. Please select a make.'})
            
            # Update item
            item.name = data.get('name')
            item.make_id = make_id
            item.model = data.get('model')
            item.type_id = data.get('type') if data.get('type') else None
            item.capacity = data.get('capacity')
            item.threshold_qty = data.get('threshold_qty') if data.get('threshold_qty') is not None else None
            item.sale_price = data.get('sale_price', 0)
            item.purchase_price = data.get('purchase_price') if data.get('purchase_price') is not None else None
            item.service_type = data.get('service_type', 'Goods')
            item.tax_preference = data.get('tax_preference', 'Non-Taxable')
            item.unit_id = data.get('unit') if data.get('unit') else None
            item.sac_code = data.get('sac_code', '').strip() if data.get('sac_code') else None
            item.igst = data.get('igst', 0)
            item.gst = data.get('gst', 0)
            item.description = data.get('description', '')
            item.full_clean()
            item.save()

            return JsonResponse({'success': True, 'message': 'Item updated successfully'})
        except ValidationError as e:
            # Handle validation errors for multiple fields
            if e.message_dict:
                # Prioritize showing field-specific errors
                error_fields = ['name', 'make', 'capacity', 'sale_price', 'sac_code']
                for field in error_fields:
                    if field in e.message_dict:
                        error_message = e.message_dict[field][0]
                        return JsonResponse({'success': False, 'error': error_message})
                # Fallback to first error if none of the prioritized fields have errors
                error_message = list(e.message_dict.values())[0][0]
            else:
                error_message = str(e)
            return JsonResponse({'success': False, 'error': error_message})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'items/add_item_custom.html', {
        'item': item,
        'types': types,
        'makes': makes,
        'units': units,
        'is_edit': True
    })

# API endpoints for dropdown options with CRUD
@csrf_exempt
def manage_types(request):
    """API for managing types: GET list, POST create"""
    if request.method == 'GET':
        types = Type.objects.all().values('id', 'value').order_by('value')
        return JsonResponse(list(types), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if Type.objects.filter(value=value).exists():
                return JsonResponse({"error": "Type already exists"}, status=400)
            type_obj = Type.objects.create(value=value)
            return JsonResponse({
                "success": True,
                "id": type_obj.id,
                "value": type_obj.value
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def manage_types_detail(request, pk):
    """API for updating/deleting types"""
    try:
        type_obj = Type.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if Type.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({"error": "Type already exists"}, status=400)
            type_obj.value = value
            type_obj.save()
            return JsonResponse({'success': True, 'message': 'Type updated'})
        elif request.method == 'DELETE':
            type_obj.delete()
            return JsonResponse({'success': True, 'message': 'Type deleted'})
    except Type.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def manage_makes(request):
    """API for managing makes: GET list, POST create"""
    if request.method == 'GET':
        makes = Make.objects.all().values('id', 'value').order_by('value')
        return JsonResponse(list(makes), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if Make.objects.filter(value=value).exists():
                return JsonResponse({"error": "Make already exists"}, status=400)
            make_obj = Make.objects.create(value=value)
            return JsonResponse({
                "success": True,
                "id": make_obj.id,
                "value": make_obj.value
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def manage_makes_detail(request, pk):
    """API for updating/deleting makes"""
    try:
        make_obj = Make.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if Make.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({"error": "Make already exists"}, status=400)
            make_obj.value = value
            make_obj.save()
            return JsonResponse({'success': True, 'message': 'Make updated'})
        elif request.method == 'DELETE':
            make_obj.delete()
            return JsonResponse({'success': True, 'message': 'Make deleted'})
    except Make.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Make not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def manage_units(request):
    """API for managing units: GET list, POST create"""
    if request.method == 'GET':
        units = Unit.objects.all().values('id', 'value').order_by('value')
        return JsonResponse(list(units), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if Unit.objects.filter(value=value).exists():
                return JsonResponse({"error": "Unit already exists"}, status=400)
            unit_obj = Unit.objects.create(value=value)
            return JsonResponse({
                "success": True,
                "id": unit_obj.id,
                "value": unit_obj.value
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def manage_units_detail(request, pk):
    """API for updating/deleting units"""
    try:
        unit_obj = Unit.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if Unit.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({"error": "Unit already exists"}, status=400)
            unit_obj.value = value
            unit_obj.save()
            return JsonResponse({'success': True, 'message': 'Unit updated'})
        elif request.method == 'DELETE':
            unit_obj.delete()
            return JsonResponse({'success': True, 'message': 'Unit deleted'})
    except Unit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Unit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def manage_items(request):
    """API for getting items list"""
    if request.method == 'GET':
        try:
            items = Item.objects.select_related('make', 'type', 'unit').all().order_by('name')
            data = []
            for item in items:
                data.append({
                    'id': item.id,
                    'item_number': item.item_number,
                    'name': item.name,
                    'make': item.make.value if item.make else None,
                    'model': item.model,
                    'type': item.type.value if item.type else None,
                    'capacity': item.capacity,
                    'unit': item.unit.value if item.unit else None,
                    'sale_price': str(item.sale_price),
                    'purchase_price': str(item.purchase_price),
                })
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def bulk_import_view(request):
    """View for bulk importing items from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'items/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'items/bulk_import.html')
            
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
                    # Normalize headers to lowercase and strip whitespace
                    rows = []
                    for row in csv_reader:
                        normalized_row = {}
                        for key, value in row.items():
                            # Normalize key to lowercase and strip
                            normalized_key = key.strip().lower() if key else ''
                            # Handle None values and convert to string
                            if value is None:
                                normalized_row[normalized_key] = ''
                            else:
                                normalized_row[normalized_key] = str(value) if value else ''
                        rows.append(normalized_row)
                except Exception as e:
                    messages.error(request, f'Error reading CSV file: {str(e)}')
                    return render(request, 'items/bulk_import.html')
            else:
                # Parse Excel file
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(io.BytesIO(file_content))
                    sheet = workbook.active
                    
                    # Get headers from first row, convert to lowercase and strip
                    headers = []
                    for cell in sheet[1]:
                        header_value = cell.value
                        if header_value:
                            headers.append(str(header_value).strip().lower())
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
                                        row_dict[headers[i]] = str(cell_value)
                            if row_dict:  # Only add if dict is not empty
                                rows.append(row_dict)
                except ImportError:
                    messages.error(request, 'openpyxl library is required for Excel files. Please install it: pip install openpyxl')
                    return render(request, 'items/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'items/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'items/bulk_import.html')
            
            # Process rows and create items
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in enumerate(rows, start=2):  # Start from 2 (1 is header)
                try:
                    # Map CSV columns to model fields - handle None values and empty strings
                    name_raw = row.get('name', '') or ''
                    name = str(name_raw).strip() if name_raw else ''
                    
                    make_raw = row.get('make', '') or ''
                    make_value = str(make_raw).strip() if make_raw else ''
                    
                    model_raw = row.get('model', '') or ''
                    model = str(model_raw).strip() if model_raw else ''
                    
                    type_raw = row.get('type', '') or ''
                    type_value = str(type_raw).strip() if type_raw else ''
                    
                    capacity_raw = row.get('capacity', '') or ''
                    capacity = str(capacity_raw).strip() if capacity_raw else ''
                    
                    threshold_qty_raw = row.get('threshold_qty', '') or ''
                    threshold_qty = str(threshold_qty_raw).strip() if threshold_qty_raw else ''
                    
                    sale_price_raw = row.get('sale_price', '0') or '0'
                    sale_price = str(sale_price_raw).strip() if sale_price_raw else '0'
                    
                    purchase_price_raw = row.get('purchase_price', '') or ''
                    purchase_price = str(purchase_price_raw).strip() if purchase_price_raw else ''
                    
                    service_type_raw = row.get('service_type', 'Goods') or 'Goods'
                    service_type = str(service_type_raw).strip() if service_type_raw else 'Goods'
                    
                    tax_preference_raw = row.get('tax_preference', 'Non-Taxable') or 'Non-Taxable'
                    tax_preference = str(tax_preference_raw).strip() if tax_preference_raw else 'Non-Taxable'
                    
                    unit_raw = row.get('unit', '') or ''
                    unit_value = str(unit_raw).strip() if unit_raw else ''
                    
                    sac_code_raw = row.get('sac_code', '') or ''
                    sac_code = str(sac_code_raw).strip() if sac_code_raw else ''
                    
                    igst_raw = row.get('igst', '0') or '0'
                    igst = str(igst_raw).strip() if igst_raw else '0'
                    
                    gst_raw = row.get('gst', '0') or '0'
                    gst = str(gst_raw).strip() if gst_raw else '0'
                    
                    description_raw = row.get('description', '') or ''
                    description = str(description_raw).strip() if description_raw else ''
                    
                    # Validate required fields (same as add_item_custom)
                    # Check if name is empty or only whitespace
                    if not name or len(name) == 0:
                        errors.append(f'Row {idx}: Name is required (column may be empty or have only whitespace)')
                        error_count += 1
                        continue
                    
                    # Check if make is empty or only whitespace
                    if not make_value or len(make_value) == 0:
                        errors.append(f'Row {idx}: Make is required. Please select a make. (column may be empty or have only whitespace)')
                        error_count += 1
                        continue
                    
                    # Get or create Make
                    make_obj, created = Make.objects.get_or_create(value=make_value)
                    
                    # Get Type if provided
                    type_obj = None
                    if type_value:
                        type_obj, created = Type.objects.get_or_create(value=type_value)
                    
                    # Get Unit if provided
                    unit_obj = None
                    if unit_value:
                        unit_obj, created = Unit.objects.get_or_create(value=unit_value)
                    
                    # Parse numeric fields (same as add_item_custom)
                    try:
                        sale_price_val = float(sale_price) if sale_price else 0.00
                        purchase_price_val = float(purchase_price) if purchase_price else None
                        threshold_qty_val = int(threshold_qty) if threshold_qty else None
                        igst_val = float(igst) if igst else 0.00
                        gst_val = float(gst) if gst else 0.00
                    except ValueError as e:
                        errors.append(f'Row {idx}: Invalid numeric value - {str(e)}')
                        error_count += 1
                        continue
                    
                    # Validate service_type and tax_preference (same as add_item_custom)
                    if service_type not in ['Goods', 'Services']:
                        service_type = 'Goods'
                    if tax_preference not in ['Taxable', 'Non-Taxable']:
                        tax_preference = 'Non-Taxable'
                    
                    # Process sac_code (same as add_item_custom - strip if provided)
                    sac_code_processed = sac_code.strip() if sac_code else None
                    
                    # Create item (same structure as add_item_custom)
                    item = Item(
                        name=name,
                        make=make_obj,
                        model=model,
                        type=type_obj,
                        capacity=capacity,
                        threshold_qty=threshold_qty_val,
                        sale_price=sale_price_val,
                        purchase_price=purchase_price_val,
                        service_type=service_type,
                        tax_preference=tax_preference,
                        unit=unit_obj,
                        sac_code=sac_code_processed,
                        igst=igst_val,
                        gst=gst_val,
                        description=description
                    )
                    
                    # Validate and save (same as add_item_custom - uses full_clean which applies all model validations)
                    try:
                        item.full_clean()  # This will validate: name, make, capacity, sac_code as per model clean()
                        item.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors same way as add_item_custom
                        if e.message_dict:
                            # Prioritize showing field-specific errors (same priority as add_item_custom)
                            error_fields = ['name', 'make', 'capacity', 'sale_price', 'sac_code']
                            error_msg = None
                            for field in error_fields:
                                if field in e.message_dict:
                                    error_msg = f"Row {idx}: {e.message_dict[field][0]}"
                                    break
                            if not error_msg:
                                # Fallback to first error if none of the prioritized fields have errors
                                error_msg = f"Row {idx}: {list(e.message_dict.values())[0][0]}"
                        else:
                            error_msg = f"Row {idx}: {str(e)}"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    
                except Exception as e:
                    errors.append(f'Row {idx}: {str(e)}')
                    error_count += 1
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} item(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if len(errors) <= 10:
                    error_message += ' Errors: ' + '; '.join(errors)
                else:
                    error_message += f' First 10 errors: ' + '; '.join(errors[:10])
                messages.warning(request, error_message)
            
            return render(request, 'items/bulk_import.html', {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors[:20]  # Show max 20 errors
            })
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'items/bulk_import.html')
    
    return render(request, 'items/bulk_import.html')
