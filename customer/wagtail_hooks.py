from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
import json

from .models import Customer, Route, Branch, ProvinceState


@hooks.register('register_admin_urls')
def register_customer_form_url():
    return [
        path('customer/add-custom/', add_customer_custom, name='add_customer_custom'),
        path('customer/edit-custom/<int:pk>/', edit_customer_custom, name='edit_customer_custom'),
        # API endpoints for dropdown management
        path('api/customer/routes/', manage_routes, name='api_manage_routes'),
        path('api/customer/routes/<int:pk>/', manage_routes, name='api_manage_routes_detail'),
        path('api/customer/branches/', manage_branches, name='api_manage_branches'),
        path('api/customer/branches/<int:pk>/', manage_branches, name='api_manage_branches_detail'),
        path('api/customer/states/', manage_states, name='api_manage_states'),
        path('api/customer/states/<int:pk>/', manage_states, name='api_manage_states_detail'),
    ]


# @hooks.register('register_admin_menu_item')
# def register_customer_menu_item():
#     return MenuItem(
#         'Add Customer',
#         reverse('add_customer_custom'),
#         icon_name='user',
#         order=1000
#     )


def add_customer_custom(request):
    """Custom view for adding a customer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['site_id', 'site_name', 'mobile']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Validate mobile length
            mobile = data.get('mobile', '')
            if len(mobile) != 10:
                return JsonResponse({
                    'success': False,
                    'error': 'Mobile number must be exactly 10 digits'
                }, status=400)
            
            # Validate phone if provided
            phone = data.get('phone', '')
            if phone and len(phone) != 10:
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number must be exactly 10 digits'
                }, status=400)
            
            # Get foreign key objects
            province_state = None
            if data.get('province_state'):
                province_state = ProvinceState.objects.filter(id=data['province_state']).first()
            
            routes = None
            if data.get('routes'):
                routes = Route.objects.filter(id=data['routes']).first()
            
            branch = None
            if data.get('branch'):
                branch = Branch.objects.filter(id=data['branch']).first()
            
            # Handle office address sync
            office_address = data.get('office_address', '')
            same_as_site = data.get('same_as_site_address')
            if isinstance(same_as_site, str):
                same_as_site = same_as_site.lower() in ('true', 'on', '1')
            if same_as_site:
                office_address = data.get('site_address', '')

            generate_license = data.get('generate_customer_license')
            if isinstance(generate_license, str):
                generate_license = generate_license.lower() in ('true', 'on', '1')

            # Create customer
            customer = Customer.objects.create(
                site_id=data['site_id'],
                job_no=data.get('job_no', ''),
                site_name=data['site_name'],
                site_address=data.get('site_address', ''),
                email=data.get('email', ''),
                phone=phone,
                mobile=mobile,
                office_address=office_address,
                same_as_site_address=same_as_site,
                contact_person_name=data.get('contact_person_name', ''),
                designation=data.get('designation', ''),
                pin_code=data.get('pin_code', ''),
                province_state=province_state,
                city=data.get('city', ''),
                sector=data.get('sector') if data.get('sector') else None,
                routes=routes,
                branch=branch,
                handover_date=data.get('handover_date') if data.get('handover_date') else None,
                billing_name=data.get('billing_name', ''),
                generate_license_now=generate_license,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Customer created successfully',
                'customer': {
                    'id': customer.id,
                    'reference_id': customer.reference_id,
                    'site_name': customer.site_name,
                    'job_no': customer.job_no
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form
    context = {
        'is_edit': False,
        'routes': Route.objects.all(),
        'branches': Branch.objects.all(),
        'states': ProvinceState.objects.all(),
    }
    return render(request, 'customer/add_customer_custom.html', context)


def edit_customer_custom(request, pk):
    """Custom view for editing a customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update fields
            customer.site_id = data.get('site_id', customer.site_id)
            customer.job_no = data.get('job_no', customer.job_no)
            customer.site_name = data.get('site_name', customer.site_name)
            customer.site_address = data.get('site_address', customer.site_address)
            customer.email = data.get('email', customer.email)
            customer.phone = data.get('phone', customer.phone)
            customer.mobile = data.get('mobile', customer.mobile)
            customer.same_as_site_address = data.get('same_as_site_address', False)
            
            # Handle office address
            if customer.same_as_site_address:
                customer.office_address = customer.site_address
            else:
                customer.office_address = data.get('office_address', customer.office_address)
            
            customer.contact_person_name = data.get('contact_person_name', customer.contact_person_name)
            customer.designation = data.get('designation', customer.designation)
            customer.pin_code = data.get('pin_code', customer.pin_code)
            customer.city = data.get('city', customer.city)
            customer.sector = data.get('sector') if data.get('sector') else customer.sector
            customer.billing_name = data.get('billing_name', customer.billing_name)
            
            # Update foreign keys
            if data.get('province_state'):
                customer.province_state = ProvinceState.objects.filter(id=data['province_state']).first()
            
            if data.get('routes'):
                customer.routes = Route.objects.filter(id=data['routes']).first()
            
            if data.get('branch'):
                customer.branch = Branch.objects.filter(id=data['branch']).first()
            
            if data.get('handover_date'):
                customer.handover_date = data['handover_date']
            
            customer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Customer updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form
    context = {
        'is_edit': True,
        'customer': customer,
        'routes': Route.objects.all(),
        'branches': Branch.objects.all(),
        'states': ProvinceState.objects.all(),
    }
    return render(request, 'customer/add_customer_custom.html', context)


# API endpoints for dropdown management
@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_routes(request, pk=None):
    """API for managing routes"""
    if request.method == 'GET':
        routes = Route.objects.all().values('id', 'value')
        return JsonResponse(list(routes), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            route = Route.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': route.id,
                'value': route.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_routes(request, pk):
    """API for updating/deleting routes"""
    try:
        route = get_object_or_404(Route, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            route.value = data['value']
            route.save()
            return JsonResponse({'success': True, 'message': 'Route updated'})
        
        elif request.method == 'DELETE':
            route.delete()
            return JsonResponse({'success': True, 'message': 'Route deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_branches(request, pk=None):
    """API for managing branches"""
    if request.method == 'GET':
        branches = Branch.objects.all().values('id', 'value')
        return JsonResponse(list(branches), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            branch = Branch.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': branch.id,
                'value': branch.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_branches(request, pk):
    """API for updating/deleting branches"""
    try:
        branch = get_object_or_404(Branch, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            branch.value = data['value']
            branch.save()
            return JsonResponse({'success': True, 'message': 'Branch updated'})
        
        elif request.method == 'DELETE':
            branch.delete()
            return JsonResponse({'success': True, 'message': 'Branch deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_states(request, pk=None):
    """API for managing states"""
    if request.method == 'GET':
        states = ProvinceState.objects.all().values('id', 'value')
        return JsonResponse(list(states), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            state = ProvinceState.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': state.id,
                'value': state.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_states(request, pk):
    """API for updating/deleting states"""
    try:
        state = get_object_or_404(ProvinceState, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            state.value = data['value']
            state.save()
            return JsonResponse({'success': True, 'message': 'State updated'})
        
        elif request.method == 'DELETE':
            state.delete()
            return JsonResponse({'success': True, 'message': 'State deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
