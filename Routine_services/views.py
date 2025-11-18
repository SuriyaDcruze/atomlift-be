from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import RoutineService
from amc.models import AMCRoutineService

@login_required
def routine_services(request):
    """View all routine services (including AMC routine services)"""
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
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get regular routine services for this month
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(service_date__gte=start_of_month.date())
    
    # Get AMC routine services for this month
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(service_date__gte=start_of_month.date())
    
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

    # Get regular completed services
    regular_services = RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
        service_date__gte=start_of_month.date(),
        status='completed'
    )
    
    # Get AMC completed services
    amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
        service_date__gte=start_of_month.date(),
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
