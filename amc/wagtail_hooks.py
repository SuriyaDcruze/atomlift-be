from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from wagtail import hooks
from wagtail.admin.menu import MenuItem
import json
from .views import get_customer_json  # Add this import

from .models import AMC, AMCType, PaymentTerms
from customer.models import Customer
from items.models import Item


# ... (existing imports and code above) ...

@hooks.register('register_admin_urls')
def register_amc_form_url():
    return [
        path('amc/add-custom/', add_amc_custom, name='add_amc_custom'),
        path('amc/edit-custom/<int:pk>/', edit_amc_custom, name='edit_amc_custom'),
        # API endpoints for dropdown management
        path('api/amc/amc-types/', manage_amc_types, name='api_manage_amc_types'),
        path('api/amc/amc-types/<int:pk>/', manage_amc_types_detail, name='api_manage_amc_types_detail'),
        path('api/amc/payment-terms/', manage_payment_terms, name='api_manage_payment_terms'),
        path('api/amc/payment-terms/<int:pk>/', manage_payment_terms_detail, name='api_manage_payment_terms_detail'),
        # API for fetching customers
        path('api/amc/customers/', get_customers, name='api_get_customers'),
        path('api/amc/items/', get_items, name='api_get_items'),
        # New endpoint for individual customer details (for autofill)
        path('customer/customer/<int:id>/', get_customer_json, name='get_customer_json'),
    ]

# ... (rest of the file unchanged) ...


# @hooks.register('register_admin_menu_item')
# def register_amc_menu_item():
#     return MenuItem(
#         'Add AMC',
#         reverse('add_amc_custom'),
#         icon_name='calendar',
#         order=1001
#     )


def add_amc_custom(request):
    """Custom view for adding an AMC"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['customer', 'start_date', 'end_date']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Get customer
            customer = Customer.objects.filter(id=data['customer']).first()
            if not customer:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid customer selected'
                }, status=400)
            
            # Get foreign key objects
            amc_type = None
            if data.get('amc_type'):
                amc_type = AMCType.objects.filter(id=data['amc_type']).first()
            
            payment_terms = None
            if data.get('payment_terms'):
                payment_terms = PaymentTerms.objects.filter(id=data['payment_terms']).first()
            
            amc_service_item = None
            if data.get('amc_service_item'):
                amc_service_item = Item.objects.filter(id=data['amc_service_item']).first()
            
            # Validate contract generation
            generate_contract = data.get('is_generate_contract')
            if isinstance(generate_contract, str):
                generate_contract = generate_contract.lower() in ('true', 'on', '1')
            if generate_contract and not amc_service_item:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select an AMC Service Item when generating contract'
                }, status=400)

            # Create AMC
            amc = AMC.objects.create(
                customer=customer,
                amcname=data.get('amcname', ''),  # Changed from 'amc_name' to 'amcname'
                invoice_frequency=data.get('invoice_frequency', 'annually'),
                amc_type=amc_type,
                payment_terms=payment_terms,
                start_date=data['start_date'],
                end_date=data['end_date'],
                equipment_no=data.get('equipment_no', ''),
                latitude=data.get('latitude', ''),
                notes=data.get('notes', ''),
                is_generate_contract=generate_contract,
                no_of_services=data.get('no_of_services', 12),
                amc_service_item=amc_service_item,
                price=data.get('price', 0),
                no_of_lifts=data.get('no_of_lifts', 0),
                gst_percentage=data.get('gst_percentage', 0),
                total_amount_paid=data.get('total_amount_paid', 0),
            )

            return JsonResponse({
                'success': True,
                'message': 'AMC created successfully',
                'amc': {
                    'id': amc.id,
                    'reference_id': amc.reference_id,
                    'customer': customer.site_name,
                    'redirect': True
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form
    # Check if customerId is in query params for auto-population
    customer_id = request.GET.get('customerId')
    selected_customer = None
    
    if customer_id:
        # Try to find customer by reference_id, id, or site_id
        selected_customer = Customer.objects.filter(
            reference_id=customer_id
        ).first() or Customer.objects.filter(
            id=customer_id
        ).first() or Customer.objects.filter(
            site_id=customer_id
        ).first()
    
    context = {
        'is_edit': False,
        'customers': Customer.objects.all(),
        'amc_types': AMCType.objects.all(),
        'payment_terms': PaymentTerms.objects.all(),
        'items': Item.objects.all(),
        'selected_customer': selected_customer,
        'customer_id_param': customer_id,
    }
    return render(request, 'amc/edit_amc_custom.html', context)


def edit_amc_custom(request, pk):
    """Custom view for editing an AMC"""
    amc = get_object_or_404(AMC, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update fields
            if data.get('customer'):
                customer = Customer.objects.filter(id=data['customer']).first()
                if customer:
                    amc.customer = customer
            
            amc.amcname = data.get('amcname', amc.amcname)  # Changed from 'amc_name' to 'amcname'
            amc.invoice_frequency = data.get('invoice_frequency', amc.invoice_frequency)
            amc.start_date = data.get('start_date', amc.start_date)
            amc.end_date = data.get('end_date', amc.end_date)
            amc.equipment_no = data.get('equipment_no', amc.equipment_no)
            amc.latitude = data.get('latitude', amc.latitude)
            amc.notes = data.get('notes', amc.notes)
            amc.is_generate_contract = data.get('is_generate_contract', amc.is_generate_contract)
            amc.no_of_services = data.get('no_of_services', amc.no_of_services)
            amc.price = data.get('price', amc.price)
            amc.no_of_lifts = data.get('no_of_lifts', amc.no_of_lifts)
            amc.gst_percentage = data.get('gst_percentage', amc.gst_percentage)
            amc.total_amount_paid = data.get('total_amount_paid', amc.total_amount_paid)
            
            # Update foreign keys
            if data.get('amc_type'):
                amc.amc_type = AMCType.objects.filter(id=data['amc_type']).first()
            
            if data.get('payment_terms'):
                amc.payment_terms = PaymentTerms.objects.filter(id=data['payment_terms']).first()
            
            if data.get('amc_service_item'):
                amc.amc_service_item = Item.objects.filter(id=data['amc_service_item']).first()
            
            amc.save()
            
            return JsonResponse({
                'success': True,
                'message': 'AMC updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form
    context = {
        'is_edit': True,
        'amc': amc,
        'customers': Customer.objects.all(),
        'amc_types': AMCType.objects.all(),
        'payment_terms': PaymentTerms.objects.all(),
        'items': Item.objects.all(),
    }
    return render(request, 'amc/edit_amc_custom.html', context)


# API endpoints
@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_amc_types(request):
    """API for managing AMC types"""
    if request.method == 'GET':
        amc_types = AMCType.objects.all().values('id', 'name')
        return JsonResponse(list(amc_types), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            amc_type = AMCType.objects.create(name=data['name'])
            return JsonResponse({
                'success': True,
                'id': amc_type.id,
                'name': amc_type.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_amc_types_detail(request, pk):
    """API for updating/deleting AMC types"""
    try:
        amc_type = get_object_or_404(AMCType, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            amc_type.name = data['name']
            amc_type.save()
            return JsonResponse({'success': True, 'message': 'AMC Type updated'})
        
        elif request.method == 'DELETE':
            amc_type.delete()
            return JsonResponse({'success': True, 'message': 'AMC Type deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_payment_terms(request):
    """API for managing payment terms"""
    if request.method == 'GET':
        payment_terms = PaymentTerms.objects.all().values('id', 'name')
        return JsonResponse(list(payment_terms), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_term = PaymentTerms.objects.create(name=data['name'])
            return JsonResponse({
                'success': True,
                'id': payment_term.id,
                'name': payment_term.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_payment_terms_detail(request, pk):
    """API for updating/deleting payment terms"""
    try:
        payment_term = get_object_or_404(PaymentTerms, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            payment_term.name = data['name']
            payment_term.save()
            return JsonResponse({'success': True, 'message': 'Payment Term updated'})
        
        elif request.method == 'DELETE':
            payment_term.delete()
            return JsonResponse({'success': True, 'message': 'Payment Term deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_customers(request):
    """API for getting all customers"""
    customers = Customer.objects.all().values(
        'id', 'reference_id', 'site_id', 'site_name', 'job_no', 'site_address'
    )
    return JsonResponse(list(customers), safe=False)


@require_http_methods(["GET"])
def get_items(request):
    """API for getting all items"""
    items = Item.objects.all().values('id', 'name')
    return JsonResponse(list(items), safe=False)
