from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import RoutineService
from amc.models import AMCRoutineService
from .utils import update_overdue_routine_services
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from customer.models import Customer
from django.urls import reverse
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging

logger = logging.getLogger(__name__)

@login_required
def routine_services(request):
    """View all routine services (including AMC routine services)"""
    # Auto-update overdue services
    update_overdue_routine_services()
    
    # Get regular routine services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').all()
    
    # Get AMC routine services and convert to unified format
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').all()
    
    # Combine and convert AMC services to match RoutineService format
    all_services = list(regular_services)
    
    # Add AMC services as unified service objects
    for amc_service in amc_services:
        # Create a unified service object that matches RoutineService interface
        # Set customer directly so templates can access it as service.customer
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,  # AMC services don't have direct lift association
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Sort by service date descending
    all_services.sort(key=lambda x: x.service_date, reverse=True)
    
    context = {
        'services': all_services,
        'title': 'All Routine Services'
    }
    return render(request, 'routine_services/routine_services.html', context)

@login_required
def today_routine_services(request):
    """View today's routine services (including AMC routine services)"""
    # Auto-update overdue services
    update_overdue_routine_services()

    today = timezone.now().date()
    
    # Get regular routine services for today
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(service_date=today)
    
    # Get AMC routine services for today
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(service_date=today)
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    context = {
        'services': all_services,
        'title': 'Today\'s Services'
    }
    return render(request, 'routine_services/today_services.html', context)

@login_required
def route_wise_services(request):
    """View services organized by route (including AMC routine services)"""
    # Get regular routine services
    regular_services = RoutineService.objects.select_related('customer', 'lift').all()
    
    # Get AMC routine services
    amc_services = AMCRoutineService.objects.select_related('amc__customer').all()
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Group services by customer location/route
    route_services = {}
    for service in all_services:
        # Get route from customer
        if service.is_amc_service:
            customer = service.amc.customer
        else:
            customer = service.customer
        
        # Get route from customer's city or routes field
        if customer:
            if hasattr(customer, 'city') and customer.city:
                route = customer.city.value if hasattr(customer.city, 'value') else str(customer.city)
            elif hasattr(customer, 'routes') and customer.routes:
                route = customer.routes.value if hasattr(customer.routes, 'value') else str(customer.routes)
            else:
                route = 'Unknown'
        else:
            route = 'Unknown'
        
        if route not in route_services:
            route_services[route] = []
        route_services[route].append(service)

    context = {
        'route_services': route_services,
        'title': 'Route Wise Services'
    }
    return render(request, 'routine_services/route_wise_services.html', context)

@login_required
def this_month_services(request):
    """View services for current month (including AMC routine services)"""
    # Auto-update overdue services
    update_overdue_routine_services()

    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Calculate start of next month
    start_of_next_month = (start_of_month + timedelta(days=32)).replace(day=1)
    
    # Get regular routine services for this month
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=start_of_next_month.date()
    )
    
    # Get AMC routine services for this month
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=start_of_next_month.date()
    )
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Sort by service date
    all_services.sort(key=lambda x: x.service_date)

    context = {
        'services': all_services,
        'title': 'This Month Services'
    }
    return render(request, 'routine_services/this_month_services.html', context)

@login_required
def last_month_overdue(request):
    """View overdue services from last month (including AMC routine services)"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    # Get regular overdue services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
        service_date__gte=start_of_last_month.date(),
        service_date__lt=start_of_month.date(),
        status__in=['pending', 'overdue']
    )
    
    # Get AMC overdue services
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
        service_date__gte=start_of_last_month.date(),
        service_date__lt=start_of_month.date(),
        status='overdue'
    )
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Sort by service date
    all_services.sort(key=lambda x: x.service_date)

    context = {
        'services': all_services,
        'title': 'Last Month Overdue'
    }
    return render(request, 'routine_services/last_month_overdue.html', context)

@login_required
def this_month_overdue(request):
    """View overdue services for current month (including AMC routine services)"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get regular overdue services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=today.date(),
        status__in=['pending', 'overdue']
    )
    
    # Get AMC overdue services
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=today.date(),
        status='overdue'
    )
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Sort by service date
    all_services.sort(key=lambda x: x.service_date)

    context = {
        'services': all_services,
        'title': 'This Month Overdue'
    }
    return render(request, 'routine_services/this_month_overdue.html', context)

@login_required
def this_month_completed(request):
    """View completed services for current month (including AMC routine services)"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Calculate start of next month
    start_of_next_month = (start_of_month + timedelta(days=32)).replace(day=1)

    # Get regular completed services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=start_of_next_month.date(),
        status='completed'
    )
    
    # Get AMC completed services
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=start_of_next_month.date(),
        status='completed'
    )
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Sort by service date
    all_services.sort(key=lambda x: x.service_date, reverse=True)

    context = {
        'services': all_services,
        'title': 'This Month Completed'
    }
    return render(request, 'routine_services/this_month_completed.html', context)

@login_required
def last_month_completed(request):
    """View completed services from last month (including AMC routine services)"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    # Get regular completed services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
        service_date__gte=start_of_last_month.date(),
        service_date__lt=start_of_month.date(),
        status='completed'
    )
    
    # Get AMC completed services
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
        service_date__gte=start_of_last_month.date(),
        service_date__lt=start_of_month.date(),
        status='completed'
    )
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'pk': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,  # Set directly for template access
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
            'created_at': amc_service.created_at,
            'updated_at': amc_service.updated_at,
            'completed_at': None,
            'notes': amc_service.note,
        })()
        all_services.append(unified_service)
    
    # Sort by service date
    all_services.sort(key=lambda x: x.service_date, reverse=True)

    context = {
        'services': all_services,
        'title': 'Last Month Completed'
    }
    return render(request, 'routine_services/last_month_completed.html', context)

@login_required
def pending_services(request):
    """View all pending services (including AMC routine services)"""
    # Auto-update overdue services
    update_overdue_routine_services()

    # Get regular pending services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(status='pending')
    
    # Get AMC pending services (status='due' is equivalent to pending)
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(status__in=['due', 'pending'])
    
    # Combine services
    all_services = list(regular_services)
    for amc_service in amc_services:
        unified_service = type('UnifiedService', (), {
            'id': f'amc_{amc_service.id}',
            'service_date': amc_service.service_date,
            'customer': amc_service.amc.customer,
            'lift': None,
            'service_type': f"AMC - {amc_service.amc.reference_id}",
            'status': 'pending' if amc_service.status == 'due' else amc_service.status,
            'assigned_technician': amc_service.employee_assign,
            'description': amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}",
            'is_amc_service': True,
            'amc_service': amc_service,
            'amc': amc_service.amc,
        })()
        all_services.append(unified_service)
    
    # Sort by service date
    all_services.sort(key=lambda x: x.service_date)

    context = {
        'services': all_services,
        'title': 'Pending Services'
    }
    return render(request, 'routine_services/pending_services.html', context)


# ======================================================
#  CUSTOMER MOBILE APP ROUTINE SERVICES API
# ======================================================

def calculate_duration_days(service_date):
    """Calculate duration in days from today"""
    today = timezone.now().date()
    delta = (service_date - today).days
    if delta > 0:
        return f"in {delta} Days"
    elif delta < 0:
        return f"{abs(delta)} Days ago"
    else:
        return "Today"


def format_service_data(service, is_amc=False, request=None):
    """Format service data for API response"""
    from django.urls import reverse
    from django.conf import settings
    
    # Get technician name
    technician_name = None
    if is_amc:
        if service.employee_assign:
            technician_name = service.employee_assign.get_full_name() or service.employee_assign.username
    else:
        if service.assigned_technician:
            technician_name = service.assigned_technician.get_full_name() or service.assigned_technician.username
    
    # Get code
    code = None
    if is_amc:
        code = service.amc.equipment_no if service.amc and service.amc.equipment_no else None
    else:
        if service.lift and service.lift.lift_code:
            code = service.lift.lift_code
        elif service.customer and service.customer.job_no:
            code = service.customer.job_no
    
    # Calculate duration
    duration = calculate_duration_days(service.service_date)
    
    # Get service slip URL (only for AMC completed services)
    service_slip_url = None
    if is_amc and service.status == 'completed':
        try:
            from django.urls import reverse
            relative_url = reverse('print_routine_service_certificate', args=[service.id])
            # Make it absolute URL if request is provided
            if request:
                service_slip_url = request.build_absolute_uri(relative_url)
            else:
                service_slip_url = relative_url
        except:
            pass
    
    return {
        'id': service.id,
        'service_date': service.service_date.strftime('%Y-%m-%d') if service.service_date else None,
        'service_type': f"AMC - {service.amc.reference_id}" if is_amc else (service.service_type or 'Routine Service'),
        'status': service.status,
        'technician_name': technician_name or "Not assigned Yet",
        'code': code or "Nil",
        'duration': duration,
        'service_slip_url': service_slip_url,
        'is_amc_service': is_amc
    }


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def customer_all_routine_services(request):
    """
    Get all routine services for a customer (list view for routine maintenance page)
    Query parameter: email (customer email)
    """
    email = request.GET.get('email')
    
    if not email:
        return Response(
            {'error': 'Email parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get customer by email
        customer = Customer.objects.get(email=email)
        
        # Get all regular routine services for this customer
        regular_services = RoutineService.objects.filter(
            customer=customer
        ).select_related('customer', 'lift', 'assigned_technician').order_by('-service_date')
        
        # Get all AMC routine services for this customer
        amc_services = AMCRoutineService.objects.filter(
            amc__customer=customer
        ).select_related('amc__customer', 'employee_assign', 'amc').order_by('-service_date')
        
        # Combine all services
        all_services_list = []
        
        # Add regular services
        for service in regular_services:
            service_data = format_service_data(service, is_amc=False, request=request)
            # Format date for display
            if service.service_date:
                service_data['service_date'] = service.service_date.strftime('%Y-%m-%d')
                service_data['service_date_display'] = service.service_date.strftime('%d/%m/%Y')
                # Get month name
                service_data['month'] = service.service_date.strftime('%B %Y')
            else:
                service_data['service_date'] = None
                service_data['service_date_display'] = 'N/A'
                service_data['month'] = 'N/A'
            
            # Map status
            status_mapping = {
                'completed': 'completed',
                'pending': 'due',
                'overdue': 'overdue',
                'in_progress': 'in progress',
            }
            service_data['status'] = status_mapping.get(service.status, service.status)
            
            all_services_list.append(service_data)
        
        # Add AMC services
        for service in amc_services:
            service_data = format_service_data(service, is_amc=True, request=request)
            # Format date for display
            if service.service_date:
                service_data['service_date'] = service.service_date.strftime('%Y-%m-%d')
                service_data['service_date_display'] = service.service_date.strftime('%d/%m/%Y')
                # Get month name
                service_data['month'] = service.service_date.strftime('%B %Y')
            else:
                service_data['service_date'] = None
                service_data['service_date_display'] = 'N/A'
                service_data['month'] = 'N/A'
            
            # Map AMC status to common status
            status_mapping = {
                'completed': 'completed',
                'due': 'due',
                'overdue': 'overdue',
                'pending': 'due',
            }
            service_data['status'] = status_mapping.get(service.status, service.status)
            
            all_services_list.append(service_data)
        
        # Sort by service date descending
        all_services_list.sort(key=lambda x: x.get('service_date') or '', reverse=True)
        
        response_data = {
            'services': all_services_list,
            'total_count': len(all_services_list),
            'message': 'Routine services retrieved successfully'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found with this email'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error retrieving customer routine services: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def customer_routine_services(request):
    """
    Get routine services for a customer (last service and upcoming service)
    Query parameter: email (customer email)
    """
    email = request.GET.get('email')
    
    if not email:
        return Response(
            {'error': 'Email parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get customer by email
        customer = Customer.objects.get(email=email)
        
        # Get all regular routine services for this customer
        regular_services = RoutineService.objects.filter(
            customer=customer
        ).select_related('customer', 'lift', 'assigned_technician').order_by('-service_date')
        
        # Get all AMC routine services for this customer
        amc_services = AMCRoutineService.objects.filter(
            amc__customer=customer
        ).select_related('amc__customer', 'employee_assign', 'amc').order_by('-service_date')
        
        # Combine all services
        all_services = []
        
        # Add regular services
        for service in regular_services:
            all_services.append((service.service_date, service, False))
        
        # Add AMC services
        for service in amc_services:
            all_services.append((service.service_date, service, True))
        
        # Sort by service date (descending)
        all_services.sort(key=lambda x: x[0], reverse=True)
        
        today = timezone.now().date()
        
        # Find last service (most recent service that has occurred - completed or past due)
        last_service = None
        past_services = []
        for service_date, service, is_amc in all_services:
            # Include services that are in the past (completed, overdue, or past pending)
            if service_date <= today:
                if is_amc:
                    # For AMC, include completed, overdue, or past due services
                    if service.status in ['completed', 'overdue'] or (service.status == 'due' and service_date < today):
                        past_services.append((service_date, service, True))
                else:
                    # For regular services, include completed, overdue, or past pending services
                    if service.status in ['completed', 'overdue'] or (service.status == 'pending' and service_date < today):
                        past_services.append((service_date, service, False))
        
        # Get the most recent past service
        if past_services:
            # Sort by date descending to get most recent
            past_services.sort(key=lambda x: x[0], reverse=True)
            service_date, service, is_amc = past_services[0]
            last_service = format_service_data(service, is_amc=is_amc, request=request)
            # Format date for display (DD/MM/YYYY)
            last_service['service_date'] = service_date.strftime('%d/%m/%Y') if service_date else '01/01/1970'
            # Ensure duration is calculated (should already be done in format_service_data)
            if not last_service.get('duration'):
                last_service['duration'] = calculate_duration_days(service_date)
            
            # Ensure service_slip_url is set for AMC completed services
            if is_amc and service.status == 'completed' and not last_service.get('service_slip_url'):
                try:
                    from django.urls import reverse
                    relative_url = reverse('print_routine_service_certificate', args=[service.id])
                    if request:
                        last_service['service_slip_url'] = request.build_absolute_uri(relative_url)
                    else:
                        last_service['service_slip_url'] = relative_url
                except Exception as e:
                    logger.error(f"Error generating service slip URL: {e}")
                    last_service['service_slip_url'] = None
        else:
            # If no past service found, use default
            last_service = {
                'id': None,
                'service_date': '01/01/1970',
                'service_type': 'No Service',
                'status': 'completed',
                'technician_name': 'Not assigned Yet',
                'code': 'Nil',
                'duration': '',
                'service_slip_url': None,
                'is_amc_service': False
            }
        
        # Find upcoming service (earliest upcoming service)
        upcoming_service = None
        upcoming_services = []
        for service_date, service, is_amc in all_services:
            if service_date >= today:
                if is_amc:
                    if service.status in ['due', 'pending', 'overdue']:
                        upcoming_services.append((service_date, service, True))
                else:
                    if service.status in ['pending', 'in_progress', 'overdue']:
                        upcoming_services.append((service_date, service, False))
        
        # Get the earliest upcoming service
        if upcoming_services:
            # Sort by date ascending to get earliest
            upcoming_services.sort(key=lambda x: x[0])
            service_date, service, is_amc = upcoming_services[0]
            upcoming_service = format_service_data(service, is_amc=is_amc, request=request)
            # Format date for display
            upcoming_service['service_date'] = service_date.strftime('%Y-%m-%d')
        else:
            # If no upcoming service found, use default
            upcoming_service = {
                'id': None,
                'service_date': None,
                'service_type': 'No Service',
                'status': 'pending',
                'technician_name': 'Not assigned Yet',
                'code': None,
                'duration': '',
                'service_slip_url': None,
                'is_amc_service': False
            }
        
        response_data = {
            'last_service': last_service,
            'upcoming_service': upcoming_service,
            'message': 'Routine services retrieved successfully'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found with this email'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error retrieving customer routine services: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def download_service_slip(request):
    """
    Download service slip PDF for a routine service
    Query parameters: service_id (required), email (required for customer verification)
    """
    service_id = request.GET.get('service_id')
    email = request.GET.get('email')
    is_amc = request.GET.get('is_amc', 'false').lower() == 'true'
    
    if not service_id:
        return Response(
            {'error': 'service_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not email:
        return Response(
            {'error': 'email parameter is required for verification'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get customer by email
        customer = Customer.objects.get(email=email)
        
        # Get the service
        if is_amc:
            # For AMC routine service
            try:
                service = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').get(pk=service_id)
                # Verify the service belongs to this customer
                if service.amc.customer != customer:
                    return Response(
                        {'error': 'Service does not belong to this customer'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Only allow download for completed services
                if service.status != 'completed':
                    return Response(
                        {'error': 'Service slip is only available for completed services'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                amc = service.amc
                
                # Prepare context data
                context = {
                    'company_name': 'Atom Lifts India Pvt Ltd',
                    'address': 'No.87B, Pillayar Koil Street, Mannurpet, Ambattur Indus Estate, Chennai 50., CHENNAI',
                    'phone': '9600087456',
                    'email': 'admin@atomlifts.com',
                    'amc_no': amc.reference_id if amc else 'N/A',
                    'service_date': service.service_date.strftime('%d/%m/%Y'),
                    'service_month': service.service_date.strftime('%B'),
                    'site_name': customer.site_name if customer else 'N/A',
                    'site_address': customer.site_address if customer and customer.site_address else 'N/A',
                    'assign_to': (
                        f"{service.employee_assign.first_name} {service.employee_assign.last_name}".strip()
                        or service.employee_assign.username
                        if service.employee_assign else "Unassigned"
                    ),
                    'technician_remark': service.note or '',
                    'service_provided': '',
                    'customer_remark': '',
                    'service': '',
                    'attend_date_time': '',
                    'service_status': service.get_status_display() if service.status != 'due' else 'Due',
                }
                
                # Build PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
                styles = getSampleStyleSheet()
                story = []
                
                # Header
                header_style = ParagraphStyle(
                    name='HeaderStyle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    alignment=1  # Center
                )
                story.append(Paragraph(context['company_name'], header_style))
                story.append(Paragraph(context['address'], styles['Normal']))
                story.append(Paragraph(f"Phone: {context['phone']} | Email: {context['email']}", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Certificate Title
                story.append(Paragraph("CERTIFICATE OF ROUTINE SERVICE VISIT", header_style))
                story.append(Spacer(1, 12))
                
                # Service Information
                data = [
                    ['AMC No.:', context['amc_no']],
                    ['Service Date:', context['service_date']],
                    ['Service Month:', context['service_month']],
                ]
                table = Table(data, colWidths=[100, 400])
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
                
                # Customer Information
                story.append(Paragraph("Customer Information", styles['Heading2']))
                cust_data = [
                    ['Site Name:', context['site_name']],
                    ['Site Address:', context['site_address']],
                    ['Note:', context['technician_remark']],
                ]
                cust_table = Table(cust_data, colWidths=[100, 400])
                cust_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(cust_table)
                story.append(Spacer(1, 12))
                
                # Service Details
                story.append(Paragraph("Service Details", styles['Heading2']))
                story.append(Paragraph(f"Assign To: {context['assign_to']}", styles['Normal']))
                story.append(Paragraph(f"Technician Remark: {context['technician_remark']}", styles['Normal']))
                story.append(Paragraph(f"Service Provided: {context['service_provided']}", styles['Normal']))
                story.append(Paragraph(f"Customer Remark: {context['customer_remark']}", styles['Normal']))
                story.append(Paragraph(f"Service: {context['service']}", styles['Normal']))
                story.append(Paragraph(f"Attend Date & Time: {context['attend_date_time']}", styles['Normal']))
                story.append(Paragraph(f"Service Status: {context['service_status']}", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Signatures
                story.append(Paragraph("Signatures", styles['Heading2']))
                story.append(Paragraph("Customer Signature:", styles['Normal']))
                story.append(Paragraph("___________________________", styles['Normal']))
                story.append(Spacer(1, 12))
                story.append(Paragraph("Technician Signature:", styles['Normal']))
                story.append(Paragraph("___________________________", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Build and return
                doc.build(story)
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                filename = f'Routine_Service_Certificate_{context["amc_no"]}_{service.service_date.strftime("%Y%m%d")}.pdf'
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
            except AMCRoutineService.DoesNotExist:
                return Response(
                    {'error': 'Service not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # For regular routine service - service slips are not available for regular services
            return Response(
                {'error': 'Service slip is only available for AMC routine services'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found with this email'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error downloading service slip: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
