from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import RoutineService

@login_required
def routine_services(request):
    """View all routine services"""
    services = RoutineService.objects.all()
    context = {
        'services': services,
        'title': 'All Routine Services'
    }
    return render(request, 'routine_services/routine_services.html', context)

@login_required
def today_routine_services(request):
    """View today's routine services"""
    today = timezone.now().date()
    services = RoutineService.objects.filter(service_date=today)
    context = {
        'services': services,
        'title': 'Today\'s Services'
    }
    return render(request, 'routine_services/today_services.html', context)

@login_required
def route_wise_services(request):
    """View services organized by route"""
    services = RoutineService.objects.select_related('customer', 'lift').all()
    # Group services by customer location/route
    route_services = {}
    for service in services:
        route = service.customer.location if hasattr(service.customer, 'location') else 'Unknown'
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
    """View services for current month"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    services = RoutineService.objects.filter(service_date__gte=start_of_month.date())

    context = {
        'services': services,
        'title': 'This Month Services'
    }
    return render(request, 'routine_services/this_month_services.html', context)

@login_required
def last_month_overdue(request):
    """View overdue services from last month"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    services = RoutineService.objects.filter(
        service_date__gte=start_of_last_month.date(),
        service_date__lt=start_of_month.date(),
        status__in=['pending', 'overdue']
    )

    context = {
        'services': services,
        'title': 'Last Month Overdue'
    }
    return render(request, 'routine_services/last_month_overdue.html', context)

@login_required
def this_month_overdue(request):
    """View overdue services for current month"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    services = RoutineService.objects.filter(
        service_date__gte=start_of_month.date(),
        service_date__lt=today.date(),
        status__in=['pending', 'overdue']
    )

    context = {
        'services': services,
        'title': 'This Month Overdue'
    }
    return render(request, 'routine_services/this_month_overdue.html', context)

@login_required
def this_month_completed(request):
    """View completed services for current month"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    services = RoutineService.objects.filter(
        service_date__gte=start_of_month.date(),
        status='completed'
    )

    context = {
        'services': services,
        'title': 'This Month Completed'
    }
    return render(request, 'routine_services/this_month_completed.html', context)

@login_required
def last_month_completed(request):
    """View completed services from last month"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    services = RoutineService.objects.filter(
        service_date__gte=start_of_last_month.date(),
        service_date__lt=start_of_month.date(),
        status='completed'
    )

    context = {
        'services': services,
        'title': 'Last Month Completed'
    }
    return render(request, 'routine_services/last_month_completed.html', context)

@login_required
def pending_services(request):
    """View all pending services"""
    services = RoutineService.objects.filter(status='pending')

    context = {
        'services': services,
        'title': 'Pending Services'
    }
    return render(request, 'routine_services/pending_services.html', context)
