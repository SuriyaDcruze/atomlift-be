from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
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
            
            # Get foreign key objects
            item = None
            if data.get('item'):
                item = get_object_or_404(Item, id=data['item'])
            
            site = None
            if data.get('site'):
                site = get_object_or_404(Customer, id=data['site'])
            
            amc = None
            if data.get('amc_id'):
                amc = get_object_or_404(AMC, id=data['amc_id'])
            
            employee = None
            if data.get('employee'):
                employee = get_object_or_404(CustomUser, id=data['employee'])
            
            # Create new requisition
            requisition = Requisition.objects.create(
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
            
            # Get foreign key objects
            item = None
            if data.get('item'):
                item = get_object_or_404(Item, id=data['item'])
            
            site = None
            if data.get('site'):
                site = get_object_or_404(Customer, id=data['site'])
            
            amc = None
            if data.get('amc_id'):
                amc = get_object_or_404(AMC, id=data['amc_id'])
            
            employee = None
            if data.get('employee'):
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
