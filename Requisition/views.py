from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.views.decorators.http import require_http_methods
from .models import Requisition, StockRegister
from items.models import Item
from customer.models import Customer
from amc.models import AMC
from authentication.models import CustomUser
import json

def add_requisition_custom(request):
    """Custom add requisition page"""
    items = Item.objects.all()
    customers = Customer.objects.all()
    amcs = AMC.objects.all()
    employees = CustomUser.objects.filter(groups__name='employee')

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
    employees = CustomUser.objects.filter(groups__name='employee')

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
                "site_id": customer.site_id or "",
                "reference_id": customer.reference_id or "",
                "email": customer.email or "",
                "phone": customer.phone or ""
            }
            for customer in customers
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def stock_register_view(request):
    """Display Stock Register with calculated available stock"""
    
    # Get all items
    items = Item.objects.all()
    
    # Prepare stock data for each item
    stock_data = []
    
    for idx, item in enumerate(items, start=1):
        # Calculate total inward and outward for this item
        stock_entries = StockRegister.objects.filter(item=item)
        
        total_inward = stock_entries.aggregate(
            total=Sum('inward_qty')
        )['total'] or 0
        
        total_outward = stock_entries.aggregate(
            total=Sum('outward_qty')
        )['total'] or 0
        
        available_stock = total_inward - total_outward
        
        # Calculate total value (using latest unit value if available)
        latest_entry = stock_entries.order_by('-date').first()
        unit_value = latest_entry.unit_value if latest_entry else item.sale_price
        
        stock_data.append({
            'no': idx,
            'item': item,
            'unit': item.unit.value if item.unit else 'N/A',
            'description': item.description or '-',
            'type': item.type.value if item.type else 'N/A',
            'value': unit_value,
            'inward_stock': total_inward,
            'outward_stock': total_outward,
            'available_stock': available_stock,
        })
    
    context = {
        'stock_data': stock_data,
        'title': 'Stock Register'
    }
    
    return render(request, 'requisition/stock_register.html', context)
