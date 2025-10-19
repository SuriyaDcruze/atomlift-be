import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Quotation
from customer.models import Customer
from amc.models import AMCType
from authentication.models import CustomUser
from lift.models import Lift


# quotation/views.py (relevant excerpts)
def add_quotation_custom(request):
    context = {
        'customers': Customer.objects.all().order_by('site_name'),
        'amc_types': AMCType.objects.all().order_by('name'),
        'users': CustomUser.objects.filter(groups__name='employee').order_by('username'),
        'lifts': Lift.objects.all().order_by('name'),
        'is_edit': False,
        'selected_lift_ids': '',
    }
    return render(request, 'quotation/add_quotation_custom.html', context)

def edit_quotation_custom(request, reference_id):
    quotation = get_object_or_404(Quotation, reference_id=reference_id)
    selected_lift_ids = ','.join(str(lift.id) for lift in quotation.lifts.all())
    context = {
        'quotation': quotation,
        'customers': Customer.objects.all().order_by('site_name'),
        'amc_types': AMCType.objects.all().order_by('name'),
        'users': CustomUser.objects.filter(groups__name='employee').order_by('username'),
        'lifts': Lift.objects.all().order_by('name'),
        'is_edit': True,
        'selected_lift_ids': selected_lift_ids,
    }
    return render(request, 'quotation/edit_quotation_custom.html', context)
@csrf_exempt
@require_http_methods(["POST"])
def create_quotation(request):
    """Create a new quotation"""
    try:
        data = request.POST
        
        # Get customer
        customer_id = data.get('customer')
        if not customer_id:
            return JsonResponse({"success": False, "error": "Customer is required"}, status=400)
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get AMC type if provided
        amc_type = None
        if data.get('amc_type'):
            amc_type = get_object_or_404(AMCType, id=data.get('amc_type'))
        
        # Get sales/service executive if provided
        sales_service_executive = None
        if data.get('sales_service_executive'):
            sales_service_executive = get_object_or_404(CustomUser, id=data.get('sales_service_executive'))
        
        # Create quotation
        quotation = Quotation.objects.create(
            customer=customer,
            amc_type=amc_type,
            sales_service_executive=sales_service_executive,
            type=data.get('type', 'Parts/Peripheral Quotation'),
            year_of_make=data.get('year_of_make', ''),
            remark=data.get('remark', ''),
            other_remark=data.get('other_remark', ''),
        )
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            quotation.uploads_files = request.FILES['uploads_files']
            quotation.save()
        
        # Handle date
        if data.get('date'):
            quotation.date = data.get('date')
            quotation.save()
        
        # Add selected lifts
        lift_ids = data.get('lifts', '').split(',')
        if lift_ids and lift_ids[0]:  # Check if not empty
            lifts = Lift.objects.filter(id__in=lift_ids)
            quotation.lifts.set(lifts)
        
        return JsonResponse({
            "success": True,
            "message": f"Quotation {quotation.reference_id} created successfully"
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_quotation(request, reference_id):
    """Update an existing quotation"""
    try:
        quotation = get_object_or_404(Quotation, reference_id=reference_id)
        data = request.POST
        
        # Update customer
        if data.get('customer'):
            customer = get_object_or_404(Customer, id=data.get('customer'))
            quotation.customer = customer
        
        # Update AMC type
        if data.get('amc_type'):
            amc_type = get_object_or_404(AMCType, id=data.get('amc_type'))
            quotation.amc_type = amc_type
        else:
            quotation.amc_type = None
        
        # Update sales/service executive
        if data.get('sales_service_executive'):
            sales_service_executive = get_object_or_404(CustomUser, id=data.get('sales_service_executive'))
            quotation.sales_service_executive = sales_service_executive
        else:
            quotation.sales_service_executive = None
        
        # Update other fields
        quotation.type = data.get('type', quotation.type)
        quotation.year_of_make = data.get('year_of_make', quotation.year_of_make)
        quotation.remark = data.get('remark', quotation.remark)
        quotation.other_remark = data.get('other_remark', quotation.other_remark)
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            quotation.uploads_files = request.FILES['uploads_files']
        
        # Handle date
        if data.get('date'):
            quotation.date = data.get('date')
        
        quotation.save()
        
        # Update selected lifts
        lift_ids = data.get('lifts', '').split(',')
        if lift_ids and lift_ids[0]:  # Check if not empty
            lifts = Lift.objects.filter(id__in=lift_ids)
            quotation.lifts.set(lifts)
        else:
            quotation.lifts.clear()
        
        return JsonResponse({
            "success": True,
            "message": f"Quotation {quotation.reference_id} updated successfully"
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# API endpoints for fetching dropdown options
@require_http_methods(["GET"])
def get_customers(request):
    """Get all customers"""
    try:
        customers = Customer.objects.all().order_by('site_name')
        data = [
            {"id": customer.id, "site_name": customer.site_name}
            for customer in customers
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_quotations(request):
    """Get existing quotations (minimal data for computing next reference id)"""
    try:
        quotations = Quotation.objects.all().only("reference_id").order_by("id")
        data = [
            {"reference_id": quotation.reference_id}
            for quotation in quotations
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_amc_types(request):
    """Get all AMC types"""
    try:
        amc_types = AMCType.objects.all().order_by('name')
        data = [
            {"id": amc_type.id, "name": amc_type.name}
            for amc_type in amc_types
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_executives(request):
    """Get all sales/service executives"""
    try:
        executives = CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username')
        data = []
        for user in executives:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            data.append({"id": user.id, "username": user.username, "name": full_name})
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_lifts(request):
    """Get all lifts"""
    try:
        lifts = Lift.objects.all().order_by('name')
        data = [
            {
                "id": lift.id, 
                "name": lift.name,
                "reference_id": lift.reference_id,
                "brand": str(lift.brand) if lift.brand else "N/A"
            }
            for lift in lifts
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
