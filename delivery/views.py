import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
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
            
            # Create delivery challan
            challan = DeliveryChallan.objects.create(
                customer_id=data.get('customer') or None,
                place_of_supply_id=data.get('place_of_supply') or None,
                date=data.get('date'),
                reference_number=data.get('reference_number', ''),
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
            
            # Update challan fields
            challan.customer_id = data.get('customer') if data.get('customer') else None
            challan.place_of_supply_id = data.get('place_of_supply') if data.get('place_of_supply') else None
            challan.date = data.get('date')
            challan.reference_number = data.get('reference_number', '')
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
