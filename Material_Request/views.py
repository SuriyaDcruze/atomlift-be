from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
import json
import csv
import io
from datetime import datetime
from .models import MaterialRequest
from items.models import Item

def frontend_view(request):
    """Serve the React frontend for Material Request"""
    return render(request, 'Material_Request/frontend.html')

@csrf_exempt
def material_request_list(request):
    """List all material requests or create a new one"""
    if request.method == 'GET':
        material_requests = MaterialRequest.objects.select_related('item').all()
        data = []
        for mr in material_requests:
            data.append({
                'id': mr.id,
                'date': mr.date.strftime('%Y-%m-%d'),
                'name': mr.name,
                'description': mr.description,
                'item': {
                    'id': mr.item.id,
                    'item_number': mr.item.item_number,
                    'name': mr.item.name,
                    'make': mr.item.make.value if mr.item.make else None,
                    'model': mr.item.model,
                    'type': mr.item.type.value if mr.item.type else None,
                    'capacity': mr.item.capacity,
                    'unit': mr.item.unit.value if mr.item.unit else None,
                },
                'brand': mr.brand,
                'file': mr.file,
                'added_by': mr.added_by,
                'requested_by': mr.requested_by,
            })
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_create(request):
    """Create a new material request"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Get the Item instance using the item ID
            item_id = data.get('item')
            if not item_id:
                return JsonResponse({'error': 'Item ID is required'}, status=400)

            try:
                item_instance = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                return JsonResponse({'error': 'Item not found'}, status=404)

            material_request = MaterialRequest.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                item=item_instance,  # Assign the Item instance, not just the ID
                brand=data.get('brand', ''),
                file=data.get('file', ''),
                added_by=data.get('added_by'),
                requested_by=data.get('requested_by'),
            )
            return JsonResponse({
                'id': material_request.id,
                'message': 'Material request created successfully'
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_detail(request, pk):
    """Get a specific material request"""
    if request.method == 'GET':
        try:
            material_request = get_object_or_404(MaterialRequest.objects.select_related('item'), pk=pk)
            data = {
                'id': material_request.id,
                'date': material_request.date.strftime('%Y-%m-%d'),
                'name': material_request.name,
                'description': material_request.description,
                'item': {
                    'id': material_request.item.id,
                    'item_number': material_request.item.item_number,
                    'name': material_request.item.name,
                    'make': material_request.item.make.value if material_request.item.make else None,
                    'model': material_request.item.model,
                    'type': material_request.item.type.value if material_request.item.type else None,
                    'capacity': material_request.item.capacity,
                    'unit': material_request.item.unit.value if material_request.item.unit else None,
                },
                'brand': material_request.brand,
                'file': material_request.file,
                'added_by': material_request.added_by,
                'requested_by': material_request.requested_by,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_update(request, pk):
    """Update a material request"""
    if request.method == 'PUT':
        try:
            material_request = get_object_or_404(MaterialRequest, pk=pk)
            data = json.loads(request.body)

            material_request.name = data.get('name', material_request.name)
            material_request.description = data.get('description', material_request.description)

            # Handle item foreign key update
            item_id = data.get('item')
            if item_id:
                try:
                    item_instance = Item.objects.get(pk=item_id)
                    material_request.item = item_instance
                except Item.DoesNotExist:
                    return JsonResponse({'error': 'Item not found'}, status=404)

            material_request.brand = data.get('brand', material_request.brand)
            material_request.file = data.get('file', material_request.file)
            material_request.added_by = data.get('added_by', material_request.added_by)
            material_request.requested_by = data.get('requested_by', material_request.requested_by)

            material_request.save()

            return JsonResponse({'message': 'Material request updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_delete(request, pk):
    """Delete a material request"""
    if request.method == 'DELETE':
        try:
            material_request = get_object_or_404(MaterialRequest, pk=pk)
            material_request.delete()
            return JsonResponse({'message': 'Material request deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def bulk_import_view(request):
    """View for bulk importing material requests from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'Material_Request/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'Material_Request/bulk_import.html')
            
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
                    rows = list(csv_reader)
                except Exception as e:
                    messages.error(request, f'Error reading CSV file: {str(e)}')
                    return render(request, 'Material_Request/bulk_import.html')
            else:
                # Parse Excel file
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(io.BytesIO(file_content))
                    sheet = workbook.active
                    
                    # Get headers from first row
                    headers = [cell.value for cell in sheet[1]]
                    rows = []
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        if any(cell for cell in row):  # Skip empty rows
                            rows.append(dict(zip(headers, row)))
                except ImportError:
                    messages.error(request, 'openpyxl library is required for Excel files. Please install it: pip install openpyxl')
                    return render(request, 'Material_Request/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'Material_Request/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'Material_Request/bulk_import.html')
            
            # Process rows and create material requests
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in enumerate(rows, start=2):  # Start from 2 (1 is header)
                try:
                    # Map CSV columns to model fields
                    # Expected columns: name, description, item_id (or item_number), brand, file, added_by, requested_by
                    name = str(row.get('name', '')).strip()
                    description = str(row.get('description', '')).strip()
                    item_id = row.get('item_id', '').strip()
                    item_number = row.get('item_number', '').strip()
                    brand = str(row.get('brand', '')).strip()
                    file_field = str(row.get('file', '')).strip()
                    added_by = str(row.get('added_by', '')).strip()
                    requested_by = str(row.get('requested_by', '')).strip()
                    
                    # Validate required fields
                    if not name:
                        errors.append(f'Row {idx}: Name is required')
                        error_count += 1
                        continue
                    
                    if not description:
                        errors.append(f'Row {idx}: Description is required')
                        error_count += 1
                        continue
                    
                    # Get item
                    item_instance = None
                    if item_id:
                        try:
                            item_instance = Item.objects.get(pk=int(item_id))
                        except (ValueError, Item.DoesNotExist):
                            errors.append(f'Row {idx}: Item with ID {item_id} not found')
                            error_count += 1
                            continue
                    elif item_number:
                        try:
                            item_instance = Item.objects.get(item_number=item_number)
                        except Item.DoesNotExist:
                            errors.append(f'Row {idx}: Item with number {item_number} not found')
                            error_count += 1
                            continue
                    else:
                        errors.append(f'Row {idx}: Either item_id or item_number is required')
                        error_count += 1
                        continue
                    
                    if not added_by:
                        errors.append(f'Row {idx}: Added by is required')
                        error_count += 1
                        continue
                    
                    if not requested_by:
                        errors.append(f'Row {idx}: Requested by is required')
                        error_count += 1
                        continue
                    
                    # Create material request
                    MaterialRequest.objects.create(
                        name=name,
                        description=description,
                        item=item_instance,
                        brand=brand,
                        file=file_field,
                        added_by=added_by,
                        requested_by=requested_by,
                    )
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'Row {idx}: {str(e)}')
                    error_count += 1
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} material request(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if len(errors) <= 10:
                    error_message += ' Errors: ' + '; '.join(errors)
                else:
                    error_message += f' First 10 errors: ' + '; '.join(errors[:10])
                messages.warning(request, error_message)
            
            return render(request, 'Material_Request/bulk_import.html', {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors[:20]  # Show max 20 errors
            })
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'Material_Request/bulk_import.html')
    
    return render(request, 'Material_Request/bulk_import.html')
