from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from .models import Requisition
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
            # Create new requisition
            requisition = Requisition.objects.create(
                date=data.get('date'),
                item_id=data.get('item') if data.get('item') else None,
                qty=data.get('qty', 0),
                site_id=data.get('site') if data.get('site') else None,
                amc_id=data.get('amc_id') if data.get('amc_id') else None,
                service=data.get('service', ''),
                employee_id=data.get('employee') if data.get('employee') else None,
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
            # Update requisition
            requisition.date = data.get('date')
            requisition.item_id = data.get('item') if data.get('item') else None
            requisition.qty = data.get('qty', 0)
            requisition.site_id = data.get('site') if data.get('site') else None
            requisition.amc_id = data.get('amc_id') if data.get('amc_id') else None
            requisition.service = data.get('service', '')
            requisition.employee_id = data.get('employee') if data.get('employee') else None
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
