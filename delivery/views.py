import csv
import io
from datetime import datetime, date
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import DeliveryChallan, DeliveryChallanItem, PlaceOfSupply


@csrf_exempt
def add_delivery_challan_custom(request):
    """Create a new delivery challan"""
    from customer.models import Customer
    from items.models import Item
    
    if request.method == 'POST':
        try:
            # Handle FormData with JSON data
            if 'data' in request.POST:
                data = json.loads(request.POST['data'])
            else:
                data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('customer'):
                return JsonResponse({
                    'success': False,
                    'error': 'Customer is required. Please select a customer.'
                }, status=400)
            
            # Create delivery challan
            challan = DeliveryChallan.objects.create(
                customer_id=data.get('customer'),
                place_of_supply_id=data.get('place_of_supply') or None,
                date=data.get('date'),
                challan_type=data.get('challan_type', 'Supply of Liquid Gas'),
                currency=data.get('currency', 'INR'),
                discount_amount=data.get('discount_amount', 0),
                discount_percentage=data.get('discount_percentage', 0),
                adjustment=data.get('adjustment', 0),
                customer_note=data.get('customer_note', ''),
                terms_conditions=data.get('terms_conditions', ''),
            )
            
            # Handle file upload if present
            if 'uploads_files' in request.FILES:
                challan.uploads_files = request.FILES['uploads_files']
                challan.save()
            
            # Create challan items
            for item_data in data.get('items', []):
                if not item_data.get('item'):
                    continue
                DeliveryChallanItem.objects.create(
                    challan=challan,
                    item_id=item_data.get('item'),
                    rate=item_data.get('rate', 0),
                    qty=item_data.get('qty', 1),
                    tax=item_data.get('tax', 0),
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Delivery challan created successfully',
                'challan_id': challan.reference_id
            })
            
        except ValidationError as e:
            # Handle validation errors
            if e.message_dict:
                error_fields = ['customer']
                for field in error_fields:
                    if field in e.message_dict:
                        error_message = e.message_dict[field][0]
                        return JsonResponse({'success': False, 'error': error_message}, status=400)
                error_message = list(e.message_dict.values())[0][0]
            else:
                error_message = str(e)
            return JsonResponse({'success': False, 'error': error_message}, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET: render form
    customers = Customer.objects.all().order_by('site_name')
    items = Item.objects.all().order_by('name')
    places_of_supply = PlaceOfSupply.objects.all().order_by('value')
    
    return render(request, 'delivery/add_delivery_challan_custom.html', {
        'customers': customers,
        'items': items,
        'places_of_supply': places_of_supply,
        'is_edit': False
    })


def edit_delivery_challan_custom(request, reference_id):
    """Edit an existing delivery challan"""
    from customer.models import Customer
    from items.models import Item
    
    try:
        challan = DeliveryChallan.objects.get(reference_id=reference_id)
    except DeliveryChallan.DoesNotExist:
        messages.error(request, 'Delivery challan not found')
        return render(request, '404.html')
    
    customers = Customer.objects.all().order_by('site_name')
    items = Item.objects.all().order_by('name')
    places_of_supply = PlaceOfSupply.objects.all().order_by('value')
    
    if request.method == 'POST':
        try:
            # Handle FormData with JSON data
            if 'data' in request.POST:
                data = json.loads(request.POST['data'])
            else:
                data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('customer'):
                return JsonResponse({
                    'success': False,
                    'error': 'Customer is required. Please select a customer.'
                }, status=400)
            
            # Update challan fields
            challan.customer_id = data.get('customer')
            challan.place_of_supply_id = data.get('place_of_supply') if data.get('place_of_supply') else None
            challan.date = data.get('date')
            challan.challan_type = data.get('challan_type', 'Supply of Liquid Gas')
            challan.currency = data.get('currency', 'INR')
            challan.discount_amount = data.get('discount_amount', 0)
            challan.discount_percentage = data.get('discount_percentage', 0)
            challan.adjustment = data.get('adjustment', 0)
            challan.customer_note = data.get('customer_note', '')
            challan.terms_conditions = data.get('terms_conditions', '')
            
            # Handle file upload if present
            if 'uploads_files' in request.FILES:
                challan.uploads_files = request.FILES['uploads_files']
            
            challan.save()
            
            # Update items - delete existing and create new ones
            challan.items.all().delete()
            for item_data in data.get('items', []):
                if not item_data.get('item'):
                    continue
                DeliveryChallanItem.objects.create(
                    challan=challan,
                    item_id=item_data.get('item'),
                    rate=item_data.get('rate', 0),
                    qty=item_data.get('qty', 1),
                    tax=item_data.get('tax', 0),
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Delivery challan updated successfully'
            })
            
        except ValidationError as e:
            # Handle validation errors
            if e.message_dict:
                error_fields = ['customer']
                for field in error_fields:
                    if field in e.message_dict:
                        error_message = e.message_dict[field][0]
                        return JsonResponse({'success': False, 'error': error_message}, status=400)
                error_message = list(e.message_dict.values())[0][0]
            else:
                error_message = str(e)
            return JsonResponse({'success': False, 'error': error_message}, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return render(request, 'delivery/add_delivery_challan_custom.html', {
        'challan': challan,
        'customers': customers,
        'items': items,
        'places_of_supply': places_of_supply,
        'is_edit': True
    })


@csrf_exempt
def manage_items(request):
    """API for managing items: GET list"""
    from items.models import Item
    
    if request.method == 'GET':
        items = Item.objects.all().values('id', 'name', 'sale_price').order_by('name')
        return JsonResponse(list(items), safe=False)


@csrf_exempt
def get_next_challan_number(request):
    """API to get the next delivery challan number"""
    try:
        last_challan = DeliveryChallan.objects.all().order_by('id').last()
        if last_challan and last_challan.reference_id.startswith(DeliveryChallan.REFERENCE_PREFIX):
            try:
                last_num = int(last_challan.reference_id.replace(DeliveryChallan.REFERENCE_PREFIX, '').strip())
                next_num = last_num + 1
            except (ValueError, AttributeError):
                next_num = 1
        else:
            next_num = 1
        return JsonResponse({'challan_number': f'{DeliveryChallan.REFERENCE_PREFIX}{next_num}'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def manage_place_of_supply(request):
    """API for managing place of supply: GET list, POST create"""
    if request.method == 'GET':
        places = PlaceOfSupply.objects.all().values('id', 'value').order_by('value')
        return JsonResponse(list(places), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if PlaceOfSupply.objects.filter(value=value).exists():
                return JsonResponse({"error": "Place of supply already exists"}, status=400)
            place = PlaceOfSupply.objects.create(value=value)
            return JsonResponse({
                "success": True,
                "id": place.id,
                "value": place.value
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def manage_place_of_supply_detail(request, pk):
    """API for updating/deleting place of supply"""
    try:
        place = PlaceOfSupply.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            value = data.get('value', '').strip()
            if not value:
                return JsonResponse({"error": "Value is required"}, status=400)
            if PlaceOfSupply.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({"error": "Place of supply already exists"}, status=400)
            place.value = value
            place.save()
            return JsonResponse({'success': True, 'message': 'Place of supply updated'})
        elif request.method == 'DELETE':
            place.delete()
            return JsonResponse({'success': True, 'message': 'Place of supply deleted'})
    except PlaceOfSupply.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Place of supply not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def bulk_import_view(request):
    """View for bulk importing delivery challans from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'delivery/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'delivery/bulk_import.html')
            
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
                    return render(request, 'delivery/bulk_import.html')
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
                    return render(request, 'delivery/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'delivery/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'delivery/bulk_import.html')
            
            # Process rows and create delivery challans
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
                    
                    # Required fields (from add_delivery_challan_custom requirements)
                    customer_value = row.get('customer', '') or row.get('customer_value', '') or ''
                    customer_value = str(customer_value).strip() if customer_value else ''
                    
                    # Validate required fields (same as add_delivery_challan_custom)
                    if not customer_value:
                        errors.append(f'Row {idx}: Customer is required.')
                        error_count += 1
                        continue
                    
                    # Get customer by site_name
                    from customer.models import Customer
                    customer = Customer.objects.filter(site_name=customer_value).first()
                    if not customer:
                        errors.append(f'Row {idx}: Customer "{customer_value}" not found. Please use an existing customer site name.')
                        error_count += 1
                        continue
                    
                    # Handle date (required in model)
                    date_value = row.get('date', '') or row.get('date_str', '')
                    date_parsed = None
                    if date_value:
                        date_parsed = parse_date(date_value)
                        if date_parsed is None:
                            errors.append(f'Row {idx}: Invalid date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    else:
                        # Use today's date if not provided
                        from django.utils import timezone
                        date_parsed = timezone.now().date()
                    
                    # Optional fields
                    place_of_supply_value = row.get('place_of_supply', '') or row.get('place_of_supply_value', '') or ''
                    place_of_supply_value = str(place_of_supply_value).strip() if place_of_supply_value else ''
                    
                    place_of_supply = None
                    if place_of_supply_value:
                        place_of_supply = PlaceOfSupply.objects.filter(value=place_of_supply_value).first()
                        if not place_of_supply:
                            errors.append(f'Row {idx}: Place of Supply "{place_of_supply_value}" not found. Please use an existing place of supply name.')
                            error_count += 1
                            continue
                    
                    # Challan type (optional, default: 'Supply of Liquid Gas')
                    challan_type = row.get('challan_type', 'Supply of Liquid Gas') or 'Supply of Liquid Gas'
                    valid_challan_types = ['Supply of Liquid Gas', 'Goods Supply', 'Service Delivery', 'Other']
                    if challan_type not in valid_challan_types:
                        challan_type = 'Supply of Liquid Gas'
                    
                    # Currency (optional, default: 'INR')
                    currency = row.get('currency', 'INR') or 'INR'
                    
                    # Parse numeric fields
                    discount_amount = 0.00
                    discount_amount_value = row.get('discount_amount', '0') or '0'
                    try:
                        discount_amount = float(discount_amount_value)
                        if discount_amount < 0:
                            discount_amount = 0.00
                    except (ValueError, TypeError):
                        discount_amount = 0.00
                    
                    discount_percentage = 0.00
                    discount_percentage_value = row.get('discount_percentage', '0') or '0'
                    try:
                        discount_percentage = float(discount_percentage_value)
                        if discount_percentage < 0:
                            discount_percentage = 0.00
                    except (ValueError, TypeError):
                        discount_percentage = 0.00
                    
                    adjustment = 0.00
                    adjustment_value = row.get('adjustment', '0') or '0'
                    try:
                        adjustment = float(adjustment_value)
                    except (ValueError, TypeError):
                        adjustment = 0.00
                    
                    # Text fields
                    customer_note = row.get('customer_note', '').strip() if row.get('customer_note') else ''
                    terms_conditions = row.get('terms_conditions', '').strip() if row.get('terms_conditions') else ''
                    
                    # Handle delivery challan items (optional - JSON format or comma-separated)
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
                                    qty = float(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else 1
                                    tax = float(parts[3].strip()) if len(parts) > 3 and parts[3].strip() else 0
                                    items_data.append({
                                        'item': item_name,
                                        'rate': rate,
                                        'qty': qty,
                                        'tax': tax
                                    })
                    
                    # Create delivery challan (same structure as add_delivery_challan_custom)
                    challan = DeliveryChallan.objects.create(
                        customer=customer,
                        place_of_supply=place_of_supply,
                        date=date_parsed,
                        challan_type=challan_type,
                        currency=currency,
                        discount_amount=discount_amount,
                        discount_percentage=discount_percentage,
                        adjustment=adjustment,
                        customer_note=customer_note,
                        terms_conditions=terms_conditions,
                    )
                    
                    # Add delivery challan items if provided
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
                                qty = float(item_data.get('qty', 1))
                                tax = float(item_data.get('tax', 0))
                                
                                if item_obj:
                                    DeliveryChallanItem.objects.create(
                                        challan=challan,
                                        item=item_obj,
                                        rate=rate,
                                        qty=qty,
                                        tax=tax,
                                    )
                    
                    # Note: File uploads (uploads_files) cannot be handled in bulk import
                    # Users need to upload files individually after import
                    
                    # Validate and save (uses full_clean which applies all model validations)
                    try:
                        challan.full_clean()
                        challan.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors
                        if e.message_dict:
                            error_fields = ['customer', 'date']
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
                messages.success(request, f'Successfully imported {success_count} delivery challan(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if errors:
                    error_message += ' Errors: ' + '; '.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f' ... and {len(errors) - 10} more error(s).'
                messages.error(request, error_message)
            
            return render(request, 'delivery/bulk_import.html')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return render(request, 'delivery/bulk_import.html')
    
    # GET request - render form
    return render(request, 'delivery/bulk_import.html')
