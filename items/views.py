# views.py (corrected to handle POST in list APIs, consolidated CRUD, added error checking like in lifts, renamed detail functions)
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from .models import Item, Type, Make, Unit
import json

def add_item_custom(request):
    """Custom add item page"""
    types = Type.objects.all()
    makes = Make.objects.all()
    units = Unit.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Create new item
            item = Item.objects.create(
                name=data.get('name'),
                make_id=data.get('make') if data.get('make') else None,
                model=data.get('model'),
                type_id=data.get('type') if data.get('type') else None,
                capacity=data.get('capacity'),
                threshold_qty=data.get('threshold_qty') if data.get('threshold_qty') is not None else None,
                sale_price=data.get('sale_price', 0),
                purchase_price=data.get('purchase_price') if data.get('purchase_price') is not None else None,
                service_type=data.get('service_type', 'Goods'),
                tax_preference=data.get('tax_preference', 'Non-Taxable'),
                unit_id=data.get('unit') if data.get('unit') else None,
                sac_code=data.get('sac_code'),
                igst=data.get('igst', 0),
                gst=data.get('gst', 0),
                description=data.get('description', '')
            )
            return JsonResponse({'success': True, 'message': 'Item created successfully'})
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
            # Update item
            item.name = data.get('name')
            item.make_id = data.get('make') if data.get('make') else None
            item.model = data.get('model')
            item.type_id = data.get('type') if data.get('type') else None
            item.capacity = data.get('capacity')
            item.threshold_qty = data.get('threshold_qty') if data.get('threshold_qty') is not None else None
            item.sale_price = data.get('sale_price', 0)
            item.purchase_price = data.get('purchase_price') if data.get('purchase_price') is not None else None
            item.service_type = data.get('service_type', 'Goods')
            item.tax_preference = data.get('tax_preference', 'Non-Taxable')
            item.unit_id = data.get('unit') if data.get('unit') else None
            item.sac_code = data.get('sac_code')
            item.igst = data.get('igst', 0)
            item.gst = data.get('gst', 0)
            item.description = data.get('description', '')
            item.save()

            return JsonResponse({'success': True, 'message': 'Item updated successfully'})
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
