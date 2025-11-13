from django.db import models
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from customer.models import Customer
from items.models import Item


class RoutineService(models.Model):
    """Model for routine services/maintenance schedules"""

    SERVICE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='routine_services')
    lift = models.ForeignKey('lift.Lift', on_delete=models.CASCADE, related_name='routine_services')
    service_date = models.DateField()
    service_type = models.CharField(max_length=100, help_text="Type of routine service")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=SERVICE_STATUS_CHOICES, default='pending')
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.customer.site_name if self.customer else 'Unknown'} - {self.service_type} ({self.service_date})"

    def is_overdue(self):
        """Check if service is overdue"""
        return self.service_date < timezone.now().date() and self.status not in ['completed', 'cancelled']


# ======================================================
#  WAGTAIL PAGE MODELS
# ======================================================

class RoutineServicesIndexPage(Page):
    """Parent page for all routine services"""
    
    parent_page_types = ['wagtailcore.Page']
    subpage_types = [
        'Routine_services.AllRoutineServicesPage',
        'Routine_services.TodayServicesPage',
        'Routine_services.RouteWiseServicesPage',
        'Routine_services.ThisMonthServicesPage',
        'Routine_services.LastMonthOverduePage',
        'Routine_services.ThisMonthOverduePage',
        'Routine_services.ThisMonthCompletedPage',
        'Routine_services.LastMonthCompletedPage',
        'Routine_services.PendingServicesPage',
    ]
    
    max_count = 1  # Only one index page
    
    content_panels = Page.content_panels


class AllRoutineServicesPage(Page):
    """All Routine Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        services = RoutineService.objects.all()
        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'All Routine Services'
        })
        return render(request, 'routine_services/routine_services.html', context)


class TodayServicesPage(Page):
    """Today's Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        today = timezone.now().date()
        services = RoutineService.objects.filter(service_date=today)
        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'Today\'s Services'
        })
        return render(request, 'routine_services/routine_services.html', context)


class RouteWiseServicesPage(Page):
    """Route Wise Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        services = RoutineService.objects.select_related('customer', 'lift').all()
        # Group services by customer location/route
        route_services = {}
        for service in services:
            if service.customer and service.customer.city:
                route = service.customer.city.value
            else:
                route = 'Unknown'
            if route not in route_services:
                route_services[route] = []
            route_services[route].append(service)

        context = self.get_context(request)
        context.update({
            'route_services': route_services,
            'title': 'Route Wise Services'
        })
        return render(request, 'routine_services/route_wise_services.html', context)


class ThisMonthServicesPage(Page):
    """This Month Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        services = RoutineService.objects.filter(service_date__gte=start_of_month.date())

        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'This Month Services'
        })
        return render(request, 'routine_services/routine_services.html', context)


class LastMonthOverduePage(Page):
    """Last Month Overdue Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

        services = RoutineService.objects.filter(
            service_date__gte=start_of_last_month.date(),
            service_date__lt=start_of_month.date(),
            status__in=['pending', 'overdue']
        )

        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'Last Month Overdue'
        })
        return render(request, 'routine_services/routine_services.html', context)


class ThisMonthOverduePage(Page):
    """This Month Overdue Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        services = RoutineService.objects.filter(
            service_date__gte=start_of_month.date(),
            service_date__lt=today.date(),
            status__in=['pending', 'overdue']
        )

        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'This Month Overdue'
        })
        return render(request, 'routine_services/routine_services.html', context)


class ThisMonthCompletedPage(Page):
    """This Month Completed Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        services = RoutineService.objects.filter(
            service_date__gte=start_of_month.date(),
            status='completed'
        )

        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'This Month Completed'
        })
        return render(request, 'routine_services/routine_services.html', context)


class LastMonthCompletedPage(Page):
    """Last Month Completed Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

        services = RoutineService.objects.filter(
            service_date__gte=start_of_last_month.date(),
            service_date__lt=start_of_month.date(),
            status='completed'
        )

        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'Last Month Completed'
        })
        return render(request, 'routine_services/routine_services.html', context)


class PendingServicesPage(Page):
    """Pending Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        services = RoutineService.objects.filter(status='pending')

        context = self.get_context(request)
        context.update({
            'services': services,
            'title': 'Pending Services'
        })
        return render(request, 'routine_services/routine_services.html', context)
