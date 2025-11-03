from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from wagtail import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu
from wagtail.snippets.widgets import SnippetListingButton
from datetime import date, timedelta
import json
from .views import get_customer_json  # Add this import
from . import views

from .models import AMC, AMCType
from customer.models import Customer
from items.models import Item


# ... (existing imports and code above) ...

@hooks.register('register_admin_urls')
def register_amc_form_url():
    return [
        path('amc/add-custom/', add_amc_custom, name='add_amc_custom'),
        path('amc/edit-custom/<int:pk>/', edit_amc_custom, name='edit_amc_custom'),
        # API endpoints for dropdown management (payment terms removed for now)
        path('api/amc/amc-types/', manage_amc_types, name='api_manage_amc_types'),
        path('api/amc/amc-types/<int:pk>/', manage_amc_types_detail, name='api_manage_amc_types_detail'),
        # API for fetching customers
        path('api/amc/customers/', get_customers, name='api_get_customers'),
        path('api/amc/items/', get_items, name='api_get_items'),
        # New endpoint for individual customer details (for autofill)
        path('customer/customer/<int:id>/', get_customer_json, name='get_customer_json'),
        # Read-only AMC expiry listing routes in admin
        path('amc/expiring/this-month/', views.amc_expiring_this_month, name='admin_amc_expiring_this_month'),
        path('amc/expiring/last-month/', views.amc_expiring_last_month, name='admin_amc_expiring_last_month'),
        path('amc/expiring/next-month/', views.amc_expiring_next_month, name='admin_amc_expiring_next_month'),
        # AMC renewal routes
        path('api/amc/renew-data/<int:pk>/', get_amc_renewal_data, name='get_amc_renewal_data'),
        path('api/amc/renew/', create_renewed_amc, name='create_renewed_amc'),
        path('amc/renew/<int:pk>/', renew_amc_page, name='renew_amc'),
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


# Removed separate submenu; expiry lists are inside AMC group now.


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
            
            # Payment terms removed
            
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

            # Handle optional numeric fields - allow empty/None values
            def parse_int(value, default=None):
                """Parse integer value, return None if empty/invalid"""
                if value is None or value == '':
                    return default
                try:
                    return int(value) if str(value).strip() else default
                except (ValueError, TypeError):
                    return default

            def parse_decimal(value, default=None):
                """Parse decimal value, return None if empty/invalid"""
                if value is None or value == '':
                    return default
                try:
                    return float(value) if str(value).strip() else default
                except (ValueError, TypeError):
                    return default

            no_of_services = parse_int(data.get('no_of_services'))
            price = parse_decimal(data.get('price'), default=0)
            no_of_lifts = parse_int(data.get('no_of_lifts'), default=0)
            gst_percentage = parse_decimal(data.get('gst_percentage'), default=0)
            total_amount_paid = parse_decimal(data.get('total_amount_paid'), default=0)

            # Create AMC
            amc = AMC.objects.create(
                customer=customer,
                amcname=data.get('amcname', ''),  # Changed from 'amc_name' to 'amcname'
                invoice_frequency=data.get('invoice_frequency', 'annually'),
                amc_type=amc_type,
                start_date=data['start_date'],
                end_date=data['end_date'],
                equipment_no=data.get('equipment_no', ''),
                latitude=data.get('latitude', ''),
                notes=data.get('notes', ''),
                is_generate_contract=generate_contract,
                no_of_services=no_of_services,
                amc_service_item=amc_service_item,
                price=price,
                no_of_lifts=no_of_lifts,
                gst_percentage=gst_percentage,
                total_amount_paid=total_amount_paid,
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
        'payment_terms': [],
        'items': Item.objects.all(),
        'selected_customer': selected_customer,
        'customer_id': customer_id,  # Fixed: changed from customer_id_param to customer_id
    }
    return render(request, 'amc/add_amc_custom.html', context)


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
            
            # Handle optional numeric fields - allow empty/None values
            def parse_int(value, default=None):
                """Parse integer value, return None if empty/invalid"""
                if value is None or value == '':
                    return default
                try:
                    return int(value) if str(value).strip() else default
                except (ValueError, TypeError):
                    return default

            def parse_decimal(value, default=None):
                """Parse decimal value, return None if empty/invalid"""
                if value is None or value == '':
                    return default
                try:
                    return float(value) if str(value).strip() else default
                except (ValueError, TypeError):
                    return default
            
            # Handle no_of_services - allow empty/None values
            if 'no_of_services' in data:
                amc.no_of_services = parse_int(data.get('no_of_services'))
            # If not in data, keep existing value (don't change it)
            
            if 'price' in data:
                price_val = parse_decimal(data.get('price'), default=0)
                amc.price = price_val if price_val is not None else 0
            if 'no_of_lifts' in data:
                lifts_val = parse_int(data.get('no_of_lifts'), default=0)
                amc.no_of_lifts = lifts_val if lifts_val is not None else 0
            if 'gst_percentage' in data:
                gst_val = parse_decimal(data.get('gst_percentage'), default=0)
                amc.gst_percentage = gst_val if gst_val is not None else 0
            if 'total_amount_paid' in data:
                paid_val = parse_decimal(data.get('total_amount_paid'), default=0)
                amc.total_amount_paid = paid_val if paid_val is not None else 0
            
            # Update foreign keys
            if data.get('amc_type'):
                amc.amc_type = AMCType.objects.filter(id=data['amc_type']).first()
            
            # Payment terms removed
            
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
        'payment_terms': [],
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
    """API for managing payment terms - DISABLED"""
    if request.method == 'GET':
        # Payment terms removed - return empty list
        return JsonResponse([], safe=False)
    
    elif request.method == 'POST':
        return JsonResponse({'success': False, 'error': 'Payment terms feature is disabled'}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_payment_terms_detail(request, pk):
    """API for updating/deleting payment terms - DISABLED"""
    return JsonResponse({'success': False, 'error': 'Payment terms feature is disabled'}, status=400)


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
    items = Item.objects.all().values('id', 'name', 'item_number')
    return JsonResponse(list(items), safe=False)


# AMC Renewal Feature
@hooks.register('register_snippet_listing_buttons')
def add_renew_amc_button(snippet, user, next_url=None):
    """Add 'Renew AMC' button for expired or expiring AMCs."""
    if isinstance(snippet, AMC):
        today = date.today()
        
        # Check if AMC is expired or expiring within 30 days
        if snippet.end_date:
            days_until_expiry = (snippet.end_date - today).days
            is_expired = snippet.end_date < today
            is_expiring_soon = 0 <= days_until_expiry <= 30
            
            # Only show button for expired or expiring AMCs
            if is_expired or is_expiring_soon:
                try:
                    url = reverse('renew_amc', kwargs={'pk': snippet.pk})
                except:
                    url = f"/admin/amc/renew/{snippet.pk}/"
                
                return [
                    SnippetListingButton(
                        label='Renew AMC',
                        url=url,
                        priority=90,
                        icon_name='repeat',
                    )
                ]
    return []


def renew_amc_page(request, pk):
    """Render the AMC renewal page"""
    amc = get_object_or_404(AMC.objects.select_related('customer', 'amc_type', 'payment_terms'), pk=pk)
    amc_types = AMCType.objects.all()
    
    context = {
        'amc': amc,
        'amc_types': amc_types,
    }
    return render(request, 'amc/renew_amc.html', context)


@require_http_methods(["GET"])
def get_amc_renewal_data(request, pk):
    """API to fetch AMC data for renewal"""
    # Use select_related to avoid N+1 queries
    amc = get_object_or_404(
        AMC.objects.select_related('customer', 'amc_type', 'payment_terms'),
        pk=pk
    )
    
    # Calculate new dates
    new_start_date = amc.end_date + timedelta(days=1) if amc.end_date else date.today()
    new_end_date = new_start_date + timedelta(days=365)
    
    data = {
        'customer_id': amc.customer.id,
        'customer_name': amc.customer.site_name,
        'start_date': new_start_date.strftime('%Y-%m-%d'),
        'end_date': new_end_date.strftime('%Y-%m-%d'),
        'amc_type_id': amc.amc_type.id if amc.amc_type else None,
        'amc_type_name': amc.amc_type.name if amc.amc_type else '',
        'no_of_services': amc.no_of_services,
        'price': str(amc.price),
        'notes': amc.notes or '',
        'amc_details': f"{amc.equipment_no or ''} - {amc.latitude or ''}".strip(' -'),
        'payment_terms_id': amc.payment_terms.id if amc.payment_terms else None,
        'equipment_no': amc.equipment_no or '',
        'latitude': amc.latitude or '',
        'amcname': amc.amcname or '',
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
def create_renewed_amc(request):
    """API to renew an AMC by updating existing AMC dates"""
    try:
        data = json.loads(request.body)
        
        # Get the original AMC to renew
        amc_id = data.get('amc_id')
        if not amc_id:
            return JsonResponse({'success': False, 'error': 'AMC ID is required for renewal'}, status=400)
        
        # Get the existing AMC
        try:
            existing_amc = AMC.objects.get(pk=amc_id)
        except AMC.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'AMC not found'}, status=404)
        
        # Get AMC type if provided
        if data.get('amc_type_id'):
            amc_type = AMCType.objects.filter(id=data['amc_type_id']).first()
            existing_amc.amc_type = amc_type
        
        # Update AMC with renewal data
        existing_amc.amcname = data.get('amcname', existing_amc.amcname)
        existing_amc.start_date = data['start_date']
        existing_amc.end_date = data['end_date']
        existing_amc.no_of_services = data.get('no_of_services', existing_amc.no_of_services)
        existing_amc.price = data.get('price', existing_amc.price)
        existing_amc.notes = data.get('notes', existing_amc.notes)
        existing_amc.equipment_no = data.get('equipment_no', existing_amc.equipment_no)
        existing_amc.latitude = data.get('latitude', existing_amc.latitude)
        existing_amc.invoice_frequency = data.get('invoice_frequency', existing_amc.invoice_frequency)
        existing_amc.is_generate_contract = data.get('is_generate_contract', existing_amc.is_generate_contract)
        
        # Save the updated AMC (this will recalculate totals and status)
        existing_amc.save()
        
        return JsonResponse({
            'success': True,
            'message': 'AMC renewed successfully',
            'amc': {
                'id': existing_amc.id,
                'reference_id': existing_amc.reference_id,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
