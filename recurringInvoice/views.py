import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import RecurringInvoice
from customer.models import Customer
from authentication.models import CustomUser


def add_recurring_invoice_custom(request):
    """Custom add recurring invoice page"""
    context = {
        'customers': Customer.objects.all().order_by('site_name'),
        'users': CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username'),
        'is_edit': False,
    }
    return render(request, 'recurringInvoice/add_recurring_invoice_custom.html', context)


def edit_recurring_invoice_custom(request, reference_id):
    """Custom edit recurring invoice page"""
    recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
    context = {
        'recurring_invoice': recurring_invoice,
        'customers': Customer.objects.all().order_by('site_name'),
        'users': CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username'),
        'is_edit': True,
    }
    return render(request, 'recurringInvoice/edit_recurring_invoice_custom.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_recurring_invoice(request):
    """Create a new recurring invoice"""
    try:
        data = request.POST
        
        # Get customer
        customer_id = data.get('customer')
        if not customer_id:
            return JsonResponse({"success": False, "error": "Customer is required"}, status=400)
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get sales person if provided
        sales_person = None
        if data.get('sales_person'):
            sales_person = get_object_or_404(CustomUser, id=data.get('sales_person'))
        
        # Create recurring invoice
        recurring_invoice = RecurringInvoice.objects.create(
            customer=customer,
            profile_name=data.get('profile_name', ''),
            order_number=data.get('order_number', ''),
            repeat_every=data.get('repeat_every', 'month'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date') if data.get('end_date') else None,
            sales_person=sales_person,
            billing_address=data.get('billing_address', ''),
            gst_treatment=data.get('gst_treatment', ''),
            status=data.get('status', 'active'),
        )
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            recurring_invoice.uploads_files = request.FILES['uploads_files']
            recurring_invoice.save()
        
        return JsonResponse({
            "success": True,
            "message": f"Recurring Invoice {recurring_invoice.reference_id} created successfully"
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_recurring_invoice(request, reference_id):
    """Update an existing recurring invoice"""
    try:
        recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
        data = request.POST
        
        # Update customer
        if data.get('customer'):
            customer = get_object_or_404(Customer, id=data.get('customer'))
            recurring_invoice.customer = customer
        
        # Update sales person
        if data.get('sales_person'):
            sales_person = get_object_or_404(CustomUser, id=data.get('sales_person'))
            recurring_invoice.sales_person = sales_person
        else:
            recurring_invoice.sales_person = None
        
        # Update other fields
        recurring_invoice.profile_name = data.get('profile_name', recurring_invoice.profile_name)
        recurring_invoice.order_number = data.get('order_number', recurring_invoice.order_number)
        recurring_invoice.repeat_every = data.get('repeat_every', recurring_invoice.repeat_every)
        recurring_invoice.start_date = data.get('start_date', recurring_invoice.start_date)
        recurring_invoice.end_date = data.get('end_date') if data.get('end_date') else None
        recurring_invoice.billing_address = data.get('billing_address', recurring_invoice.billing_address)
        recurring_invoice.gst_treatment = data.get('gst_treatment', recurring_invoice.gst_treatment)
        recurring_invoice.status = data.get('status', recurring_invoice.status)
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            recurring_invoice.uploads_files = request.FILES['uploads_files']
        
        recurring_invoice.save()
        
        return JsonResponse({
            "success": True,
            "message": f"Recurring Invoice {recurring_invoice.reference_id} updated successfully"
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
def get_recurring_invoices(request):
    """Get existing recurring invoices (minimal data for computing next reference id)"""
    try:
        recurring_invoices = RecurringInvoice.objects.all().only("reference_id").order_by("id")
        data = [
            {"reference_id": recurring_invoice.reference_id}
            for recurring_invoice in recurring_invoices
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_sales_persons(request):
    """Get all sales persons"""
    try:
        sales_persons = CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username')
        data = []
        for user in sales_persons:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            data.append({"id": user.id, "username": user.username, "name": full_name})
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
