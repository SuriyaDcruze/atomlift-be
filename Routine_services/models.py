from django.db import models
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, date
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
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
    
    def cust_refno(self):
        """Customer reference number (job_no or reference_id)"""
        if self.customer:
            return self.customer.job_no or self.customer.reference_id
        return "—"
    cust_refno.short_description = "Cust_refno"
    
    def lift_code(self):
        """Lift code from lift"""
        if self.lift and self.lift.lift_code:
            return self.lift.lift_code
        return "—"
    lift_code.short_description = "Lift Code"
    
    def routes(self):
        """Routes from customer"""
        if self.customer and hasattr(self.customer, 'routes'):
            if self.customer.routes:
                if hasattr(self.customer.routes, 'all'):
                    # ManyToMany field
                    return ", ".join(str(route) for route in self.customer.routes.all())
                elif hasattr(self.customer.routes, 'value'):
                    return str(self.customer.routes.value)
                return str(self.customer.routes)
        return "—"
    routes.short_description = "Routes"
    
    def block_wing(self):
        """Block/Wing - not available for regular services"""
        return "—"
    block_wing.short_description = "Block/Wing"
    
    def employee(self):
        """Employee/technician name with edit button"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        employee_name = "—"
        if self.assigned_technician:
            if hasattr(self.assigned_technician, 'get_full_name'):
                full_name = self.assigned_technician.get_full_name()
                if full_name:
                    employee_name = full_name
                else:
                    employee_name = self.assigned_technician.username
            else:
                employee_name = self.assigned_technician.username
        
        # Create edit button for regular routine service
        return format_html(
            '<span class="employee-display" data-service-id="{}" data-service-type="regular">'
            '{} <button class="employee-edit-btn" onclick="editEmployee(this, {}, \'regular\')" title="Edit Employee">✏️</button>'
            '</span>',
            self.id,
            employee_name,
            self.id
        )
    employee.short_description = "Employee"
    employee.allow_tags = True
    
    def service_date_display(self):
        """Service date with edit button"""
        from django.utils.html import format_html
        
        date_str = self.service_date.strftime('%d/%m/%Y') if self.service_date else "—"
        
        return format_html(
            '<span class="service-date-display" data-service-id="{}" data-service-type="regular">'
            '{} <button class="date-edit-btn" onclick="editServiceDate(this, {}, \'regular\')" title="Edit Service Date" style="background:none;border:none;cursor:pointer;padding:2px 4px;">✏️</button>'
            '</span>',
            self.id,
            date_str,
            self.id
        )
    service_date_display.short_description = "Service Date"
    service_date_display.allow_tags = True
    
    def gmap(self):
        """Google Maps link"""
        if self.customer and self.customer.latitude and self.customer.longitude:
            lat = float(self.customer.latitude)
            lon = float(self.customer.longitude)
            return f"https://www.google.com/maps?q={lat},{lon}"
        return "—"
    gmap.short_description = "GMAP"
    
    def location(self):
        """Location (site address)"""
        if self.customer and self.customer.site_address:
            return self.customer.site_address
        return "—"
    location.short_description = "Location"
    
    def print_link(self):
        """Download PDF link - not available for regular services"""
        return "—"
    print_link.short_description = "Print"


# ======================================================
#  PROXY MODELS FOR WAGTAIL SNIPPET VIEWSETS
# ======================================================

class RoutineServiceThisMonthExpiring(RoutineService):
    """Proxy model for routine services expiring this month"""
    class Meta:
        proxy = True
        verbose_name = "This Month Expiring Routine Service"
        verbose_name_plural = "This Month Expiring Routine Services"


class RoutineServiceLastMonthExpiring(RoutineService):
    """Proxy model for routine services that expired last month"""
    class Meta:
        proxy = True
        verbose_name = "Last Month Expired Routine Service"
        verbose_name_plural = "Last Month Expired Routine Services"


class RoutineServiceAll(RoutineService):
    """Proxy model for all routine services"""
    class Meta:
        proxy = True
        verbose_name = "All Routine Service"
        verbose_name_plural = "All Routine Services"


class RoutineServiceToday(RoutineService):
    """Proxy model for today's routine services"""
    class Meta:
        proxy = True
        verbose_name = "Today's Routine Service"
        verbose_name_plural = "Today's Routine Services"


class RoutineServiceRouteWise(RoutineService):
    """Proxy model for route-wise routine services"""
    class Meta:
        proxy = True
        verbose_name = "Route Wise Routine Service"
        verbose_name_plural = "Route Wise Routine Services"


class RoutineServiceThisMonth(RoutineService):
    """Proxy model for this month's routine services"""
    class Meta:
        proxy = True
        verbose_name = "This Month Routine Service"
        verbose_name_plural = "This Month Routine Services"


class RoutineServiceLastMonthOverdue(RoutineService):
    """Proxy model for last month's overdue routine services"""
    class Meta:
        proxy = True
        verbose_name = "Last Month Overdue Routine Service"
        verbose_name_plural = "Last Month Overdue Routine Services"


class RoutineServiceThisMonthOverdue(RoutineService):
    """Proxy model for this month's overdue routine services"""
    class Meta:
        proxy = True
        verbose_name = "This Month Overdue Routine Service"
        verbose_name_plural = "This Month Overdue Routine Services"


class RoutineServiceThisMonthCompleted(RoutineService):
    """Proxy model for this month's completed routine services"""
    class Meta:
        proxy = True
        verbose_name = "This Month Completed Routine Service"
        verbose_name_plural = "This Month Completed Routine Services"


class RoutineServiceLastMonthCompleted(RoutineService):
    """Proxy model for last month's completed routine services"""
    class Meta:
        proxy = True
        verbose_name = "Last Month Completed Routine Service"
        verbose_name_plural = "Last Month Completed Routine Services"


class RoutineServicePending(RoutineService):
    """Proxy model for pending routine services"""
    class Meta:
        proxy = True
        verbose_name = "Pending Routine Service"
        verbose_name_plural = "Pending Routine Services"


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
        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').all())
        
        # Get AMC routine services and convert to unified format
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').all()
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)
        
        context = self.get_context(request)
        context.update({
            'services': regular_services,
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
        # Get regular routine services for today
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(service_date=today))
        
        # Get AMC routine services for today
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(service_date=today)
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        context = self.get_context(request)
        context.update({
            'services': regular_services,
            'title': 'Today\'s Services'
        })
        return render(request, 'routine_services/routine_services.html', context)


class UnifiedService:
    """Wrapper class to make AMC routine services compatible with Wagtail list display"""
    def __init__(self, amc_service):
        self.id = f'amc_{amc_service.id}'
        self.pk = f'amc_{amc_service.id}'
        self.service_date = amc_service.service_date
        self.customer = amc_service.amc.customer
        self.lift = None  # AMC services don't have direct lift association
        self.service_type = f"AMC - {amc_service.amc.reference_id}"
        self.status = amc_service.status
        self.assigned_technician = amc_service.employee_assign
        self.description = amc_service.note or f"AMC Routine Service for {amc_service.amc.reference_id}"
        self.is_amc_service = True
        self.amc_service = amc_service
        self.amc = amc_service.amc
        self.block_wing = amc_service.block_wing
        self.created_at = amc_service.created_at
        self.updated_at = amc_service.updated_at
        self.completed_at = None
        self.notes = amc_service.note
        # Store original for reference
        self._amc_service = amc_service
    
    def __str__(self):
        return f"{self.customer.site_name if self.customer else 'Unknown'} - {self.service_type} ({self.service_date})"
    
    def cust_refno(self):
        """Customer reference number (job_no or reference_id)"""
        if self.customer:
            return self.customer.job_no or self.customer.reference_id
        return "—"
    cust_refno.short_description = "Cust_refno"
    
    def lift_code(self):
        """Lift code from AMC equipment_no or customer job_no"""
        if self.amc and self.amc.equipment_no:
            return self.amc.equipment_no
        if self.customer and self.customer.job_no:
            return self.customer.job_no
        return "—"
    lift_code.short_description = "Lift Code"
    
    def routes(self):
        """Routes from customer"""
        if self.customer and hasattr(self.customer, 'routes'):
            if self.customer.routes:
                if hasattr(self.customer.routes, 'all'):
                    # ManyToMany field
                    return ", ".join(str(route) for route in self.customer.routes.all())
                elif hasattr(self.customer.routes, 'value'):
                    return str(self.customer.routes.value)
                return str(self.customer.routes)
        return "—"
    routes.short_description = "Routes"
    
    def employee(self):
        """Employee/technician name with edit button"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        employee_name = "—"
        if self.assigned_technician:
            if hasattr(self.assigned_technician, 'get_full_name'):
                full_name = self.assigned_technician.get_full_name()
                if full_name:
                    employee_name = full_name
                else:
                    employee_name = self.assigned_technician.username
            else:
                employee_name = self.assigned_technician.username
        
        # Extract actual AMC service ID from the unified service ID
        amc_service_id = self._amc_service.id if hasattr(self, '_amc_service') else None
        
        # Create edit button for AMC routine service
        return format_html(
            '<span class="employee-display" data-service-id="{}" data-service-type="amc" data-amc-service-id="{}">'
            '{} <button class="employee-edit-btn" onclick="editEmployee(this, {}, \'amc\')" title="Edit Employee">✏️</button>'
            '</span>',
            self.id,
            amc_service_id or '',
            employee_name,
            amc_service_id or self.id
        )
    employee.short_description = "Employee"
    employee.allow_tags = True
    
    def service_date_display(self):
        """Service date with edit button"""
        from django.utils.html import format_html
        
        amc_service = self._amc_service if hasattr(self, '_amc_service') else None
        service_date = amc_service.service_date if amc_service and amc_service.service_date else None
        
        date_str = service_date.strftime('%d/%m/%Y') if service_date else "—"
        amc_service_id = amc_service.id if amc_service else None
        
        return format_html(
            '<span class="service-date-display" data-service-id="{}" data-service-type="amc" data-amc-service-id="{}">'
            '{} <button class="date-edit-btn" onclick="editServiceDate(this, {}, \'amc\')" title="Edit Service Date" style="background:none;border:none;cursor:pointer;padding:2px 4px;">✏️</button>'
            '</span>',
            self.id,
            amc_service_id or '',
            date_str,
            amc_service_id or self.id
        )
    service_date_display.short_description = "Service Date"
    service_date_display.allow_tags = True
    
    def gmap(self):
        """Google Maps link"""
        if self.customer and self.customer.latitude and self.customer.longitude:
            lat = float(self.customer.latitude)
            lon = float(self.customer.longitude)
            return f"https://www.google.com/maps?q={lat},{lon}"
        return "—"
    gmap.short_description = "GMAP"
    
    def location(self):
        """Location (site address)"""
        if self.customer and self.customer.site_address:
            return self.customer.site_address
        return "—"
    location.short_description = "Location"
    
    def print_link(self):
        """Download PDF link with icon"""
        from django.utils.html import format_html
        from django.urls import reverse
        try:
            pdf_url = reverse('print_routine_service_certificate', args=[self._amc_service.id])
            return format_html(
                '<a href="{}" target="_blank" class="download-pdf-link" title="Download as PDF">'
                '<svg class="icon icon-download w-icon" aria-hidden="true" focusable="false">'
                '<use href="#icon-download"></use>'
                '</svg>'
                '</a>',
                pdf_url
            )
        except:
            return "—"
    print_link.short_description = "Print"
    print_link.allow_tags = True
    
    def __getattr__(self, name):
        # Fallback for any missing attributes
        if hasattr(self._amc_service, name):
            return getattr(self._amc_service, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def _create_unified_service_from_amc(amc_service):
    """Helper function to create unified service object from AMC routine service"""
    return UnifiedService(amc_service)


class RouteWiseServicesPage(Page):
    """Route Wise Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift').all())
        
        # Get AMC routine services and convert to unified format
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer').all()
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Group services by customer location/route
        route_services = {}
        for service in regular_services:
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
        # Get regular routine services for this month
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(service_date__gte=start_of_month.date()))
        
        # Get AMC routine services for this month
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(service_date__gte=start_of_month.date())
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)

        context = self.get_context(request)
        context.update({
            'services': regular_services,
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

        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
            service_date__gte=start_of_last_month.date(),
            service_date__lt=start_of_month.date(),
            status__in=['pending', 'overdue']
        ))
        
        # Get AMC routine services
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
                service_date__gte=start_of_last_month.date(),
                service_date__lt=start_of_month.date(),
                status__in=['due', 'overdue']
            )
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)

        context = self.get_context(request)
        context.update({
            'services': regular_services,
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

        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
            service_date__gte=start_of_month.date(),
            service_date__lt=today.date(),
            status__in=['pending', 'overdue']
        ))
        
        # Get AMC routine services
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
                service_date__gte=start_of_month.date(),
                service_date__lt=today.date(),
                status__in=['due', 'overdue']
            )
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)

        context = self.get_context(request)
        context.update({
            'services': regular_services,
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

        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
            service_date__gte=start_of_month.date(),
            status='completed'
        ))
        
        # Get AMC routine services
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
                service_date__gte=start_of_month.date(),
                status='completed'
            )
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)

        context = self.get_context(request)
        context.update({
            'services': regular_services,
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

        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(
            service_date__gte=start_of_last_month.date(),
            service_date__lt=start_of_month.date(),
            status='completed'
        ))
        
        # Get AMC routine services
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(
                service_date__gte=start_of_last_month.date(),
                service_date__lt=start_of_month.date(),
                status='completed'
            )
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)

        context = self.get_context(request)
        context.update({
            'services': regular_services,
            'title': 'Last Month Completed'
        })
        return render(request, 'routine_services/routine_services.html', context)


class PendingServicesPage(Page):
    """Pending Services Page"""
    
    parent_page_types = ['Routine_services.RoutineServicesIndexPage']
    subpage_types = []
    
    content_panels = Page.content_panels
    
    def serve(self, request, *args, **kwargs):
        # Get regular routine services
        regular_services = list(RoutineService.objects.select_related('customer', 'lift', 'assigned_technician').filter(status='pending'))
        
        # Get AMC routine services
        try:
            from amc.models import AMCRoutineService
            amc_services = AMCRoutineService.objects.select_related('amc__customer', 'employee_assign').filter(status='due')
            for amc_service in amc_services:
                unified_service = _create_unified_service_from_amc(amc_service)
                regular_services.append(unified_service)
        except ImportError:
            pass
        
        # Sort by service date descending
        regular_services.sort(key=lambda x: x.service_date, reverse=True)

        context = self.get_context(request)
        context.update({
            'services': regular_services,
            'title': 'Pending Services'
        })
        return render(request, 'routine_services/routine_services.html', context)


# ======================================================
#  WAGTAIL SNIPPET VIEWSETS
# ======================================================

class RoutineServiceThisMonthExpiringViewSet(SnippetViewSet):
    model = RoutineServiceThisMonthExpiring
    icon = "date"
    menu_label = "This Month Expiring"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None  # Hide the add button from list view header

    list_display = (
        "customer",
        "lift",
        "service_type",
        "service_date",
        "status",
        "assigned_technician",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        first_day = today.replace(day=1)
        if first_day.month == 12:
            next_month_first = first_day.replace(year=first_day.year + 1, month=1, day=1)
        else:
            next_month_first = first_day.replace(month=first_day.month + 1, day=1)
        last_day = next_month_first - timedelta(days=1)
        return RoutineService.objects.filter(
            service_date__gte=first_day, 
            service_date__lte=last_day
        ).order_by("service_date")
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add/edit/delete permissions"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddRoutineServiceExpiringPermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding/editing/deleting routine service expiring records"""
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddRoutineServiceExpiringPermissionPolicy(self.model)


class RoutineServiceLastMonthExpiringViewSet(SnippetViewSet):
    model = RoutineServiceLastMonthExpiring
    icon = "date"
    menu_label = "Last Month Expired"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None  # Hide the add button from list view header

    list_display = (
        "customer",
        "lift",
        "service_type",
        "service_date",
        "status",
        "assigned_technician",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        first_of_this_month = today.replace(day=1)
        last_month_last_day = first_of_this_month - timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)
        return RoutineService.objects.filter(
            service_date__gte=last_month_first_day, 
            service_date__lte=last_month_last_day
        ).order_by("service_date")
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add/edit/delete permissions"""
        from wagtail.permissions import ModelPermissionPolicy
        
        class NoAddRoutineServiceExpiringPermissionPolicy(ModelPermissionPolicy):
            """Custom permission policy that disallows adding/editing/deleting routine service expiring records"""
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        
        return NoAddRoutineServiceExpiringPermissionPolicy(self.model)


# ======================================================
#  MAIN ROUTINE SERVICE VIEWSET (with add/edit/delete)
# ======================================================

class RoutineServiceViewSet(SnippetViewSet):
    model = RoutineService
    icon = "cog"
    menu_label = "All Routine Services"
    inspect_view_enabled = True

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedIndexView
        return RoutineService.objects.none()

    # Custom IndexView to include AMC routine services
    class CombinedIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list"""
            # Get regular routine services
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).all())
            
            # Get AMC routine services and convert to unified format
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).all()
                
                # Use the helper function to create unified service objects for AMC services
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass  # AMC app not available
            
            # Sort by service date descending
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            
            # Get combined services
            all_services = self.get_queryset()
            
            # Apply pagination
            paginator = Paginator(all_services, 20)  # 20 items per page
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            
            # Get the base context
            context = super().get_context_data(**kwargs)
            
            # Override with our combined and paginated services
            # Wagtail's template iterates over object_list, so use the actual list
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            
            return context
    
    index_view_class = CombinedIndexView


# ======================================================
#  FILTERED ROUTINE SERVICE VIEWSETS (read-only)
# ======================================================

class RoutineServiceTodayViewSet(SnippetViewSet):
    model = RoutineServiceToday
    icon = "date"
    menu_label = "Today's Services"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "assigned_technician",
        "lift",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedTodayIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedTodayIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for today's services"""
            today = timezone.now().date()
            
            # Get regular routine services for today
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(service_date=today))
            
            # Get AMC routine services for today and convert to unified format
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(service_date=today)
                
                # Use the helper function to create unified service objects for AMC services
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass  # AMC app not available
            
            # Sort by service date descending
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            
            # Get combined services
            all_services = self.get_queryset()
            
            # Apply pagination
            paginator = Paginator(all_services, 20)  # 20 items per page
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            
            # Get the base context
            context = super().get_context_data(**kwargs)
            
            # Override with our combined and paginated services
            # Wagtail's template iterates over object_list, so use the actual list
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            
            return context
    
    index_view_class = CombinedTodayIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServiceThisMonthViewSet(SnippetViewSet):
    model = RoutineServiceThisMonth
    icon = "date"
    menu_label = "This Month Services"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedThisMonthIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedThisMonthIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for this month's services"""
            today = timezone.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get regular routine services for this month
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(service_date__gte=start_of_month.date()))
            
            # Get AMC routine services for this month and convert to unified format
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(service_date__gte=start_of_month.date())
                
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass
            
            # Sort by service date descending
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            all_services = self.get_queryset()
            paginator = Paginator(all_services, 20)
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            context = super().get_context_data(**kwargs)
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            return context
    
    index_view_class = CombinedThisMonthIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServiceLastMonthOverdueViewSet(SnippetViewSet):
    model = RoutineServiceLastMonthOverdue
    icon = "warning"
    menu_label = "Last Month Overdue"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedLastMonthOverdueIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedLastMonthOverdueIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for last month's overdue services"""
            today = timezone.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
            
            # Get regular routine services
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(
                service_date__gte=start_of_last_month.date(),
                service_date__lt=start_of_month.date(),
                status__in=['pending', 'overdue']
            ))
            
            # Get AMC routine services
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(
                    service_date__gte=start_of_last_month.date(),
                    service_date__lt=start_of_month.date(),
                    status__in=['due', 'overdue']
                )
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass
            
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            all_services = self.get_queryset()
            paginator = Paginator(all_services, 20)
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            context = super().get_context_data(**kwargs)
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            return context
    
    index_view_class = CombinedLastMonthOverdueIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServiceThisMonthOverdueViewSet(SnippetViewSet):
    model = RoutineServiceThisMonthOverdue
    icon = "warning"
    menu_label = "This Month Overdue"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedThisMonthOverdueIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedThisMonthOverdueIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for this month's overdue services"""
            today = timezone.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get regular routine services
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(
                service_date__gte=start_of_month.date(),
                service_date__lt=today.date(),
                status__in=['pending', 'overdue']
            ))
            
            # Get AMC routine services
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(
                    service_date__gte=start_of_month.date(),
                    service_date__lt=today.date(),
                    status__in=['due', 'overdue']
                )
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass
            
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            all_services = self.get_queryset()
            paginator = Paginator(all_services, 20)
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            context = super().get_context_data(**kwargs)
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            return context
    
    index_view_class = CombinedThisMonthOverdueIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServiceThisMonthCompletedViewSet(SnippetViewSet):
    model = RoutineServiceThisMonthCompleted
    icon = "calendar-alt"
    menu_label = "This Month Completed"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedThisMonthCompletedIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedThisMonthCompletedIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for this month's completed services"""
            today = timezone.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get regular routine services
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(
                service_date__gte=start_of_month.date(),
                status='completed'
            ))
            
            # Get AMC routine services
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(
                    service_date__gte=start_of_month.date(),
                    status='completed'
                )
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass
            
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            all_services = self.get_queryset()
            paginator = Paginator(all_services, 20)
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            context = super().get_context_data(**kwargs)
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            return context
    
    index_view_class = CombinedThisMonthCompletedIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServiceLastMonthCompletedViewSet(SnippetViewSet):
    model = RoutineServiceLastMonthCompleted
    icon = "calendar-check"
    menu_label = "Last Month Completed"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedLastMonthCompletedIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedLastMonthCompletedIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for last month's completed services"""
            today = timezone.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
            
            # Get regular routine services
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(
                service_date__gte=start_of_last_month.date(),
                service_date__lt=start_of_month.date(),
                status='completed'
            ))
            
            # Get AMC routine services
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(
                    service_date__gte=start_of_last_month.date(),
                    service_date__lt=start_of_month.date(),
                    status='completed'
                )
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass
            
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            all_services = self.get_queryset()
            paginator = Paginator(all_services, 20)
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            context = super().get_context_data(**kwargs)
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            return context
    
    index_view_class = CombinedLastMonthCompletedIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServicePendingViewSet(SnippetViewSet):
    model = RoutineServicePending
    icon = "time"
    menu_label = "Pending Services"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "cust_refno",
        "lift_code",
        "routes",
        "block_wing",
        "customer",
        "service_date_display",
        "gmap",
        "employee",
        "status",
        "location",
        "print_link",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        # Return empty queryset - we'll handle everything in CombinedPendingIndexView
        return RoutineService.objects.none()
    
    # Custom IndexView to include AMC routine services
    class CombinedPendingIndexView(IndexView):
        def get_queryset(self):
            """Override to return combined queryset-like list for pending services"""
            # Get regular routine services
            regular_services = list(RoutineService.objects.select_related(
                'customer', 'lift', 'assigned_technician'
            ).filter(status='pending'))
            
            # Get AMC routine services (status='due' is equivalent to pending)
            try:
                from amc.models import AMCRoutineService
                amc_services = AMCRoutineService.objects.select_related(
                    'amc__customer', 'employee_assign'
                ).filter(status__in=['due', 'pending'])
                for amc_service in amc_services:
                    unified_service = _create_unified_service_from_amc(amc_service)
                    regular_services.append(unified_service)
            except ImportError:
                pass
            
            regular_services.sort(key=lambda x: x.service_date, reverse=True)
            return regular_services
        
        def get_context_data(self, **kwargs):
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            all_services = self.get_queryset()
            paginator = Paginator(all_services, 20)
            page = self.request.GET.get('p', 1)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            context = super().get_context_data(**kwargs)
            context['object_list'] = list(page_obj)
            context['page_obj'] = page_obj
            return context
    
    index_view_class = CombinedPendingIndexView
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


class RoutineServiceRouteWiseViewSet(SnippetViewSet):
    model = RoutineServiceRouteWise
    icon = "calendar-alt"
    menu_label = "Route Wise Services"
    inspect_view_enabled = True
    create_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    list_display_add_buttons = None

    list_display = (
        "customer",
        "lift",
        "service_type",
        "service_date",
        "status",
        "assigned_technician",
    )

    list_export = [
        "id",
        "customer",
        "lift",
        "service_type",
        "service_date",
        "description",
        "status",
        "assigned_technician",
        "created_at",
        "updated_at",
        "completed_at",
        "notes",
    ]
    export_formats = ["csv", "xlsx"]

    search_fields = (
        "customer__site_name",
        "customer__city__value",
        "lift__reference_id",
        "lift__lift_code",
        "lift__name",
        "service_type",
        "description",
    )

    list_filter = (
        "customer__city",
        "status",
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
    )

    def get_queryset(self, request):
        return RoutineService.objects.select_related('customer', 'lift').all().order_by("customer__city", "service_date")
    
    @property
    def permission_policy(self):
        from wagtail.permissions import ModelPermissionPolicy
        class NoAddPermissionPolicy(ModelPermissionPolicy):
            def user_has_permission(self, user, action):
                if action in ["add", "edit", "delete"]:
                    return False
                return super().user_has_permission(user, action)
        return NoAddPermissionPolicy(self.model)


# ======================================================
#  SNIPPET VIEWSET GROUPS
# ======================================================

class RoutineServiceExpiringGroup(SnippetViewSetGroup):
    menu_label = "Routine Services Expiring"
    menu_icon = "date"
    menu_order = 200
    items = (
        RoutineServiceThisMonthExpiringViewSet,
        RoutineServiceLastMonthExpiringViewSet,
    )


class RoutineServiceManagementGroup(SnippetViewSetGroup):
    menu_label = "Routine Services"
    menu_icon = "cog"
    menu_order = 7  # Position below Sales (order=6)
    items = (
        RoutineServiceViewSet,
        RoutineServiceTodayViewSet,
        RoutineServiceThisMonthViewSet,
        RoutineServiceRouteWiseViewSet,
        RoutineServicePendingViewSet,
        RoutineServiceThisMonthOverdueViewSet,
        RoutineServiceLastMonthOverdueViewSet,
        RoutineServiceThisMonthCompletedViewSet,
        RoutineServiceLastMonthCompletedViewSet,
    )


register_snippet(RoutineServiceExpiringGroup)
register_snippet(RoutineServiceManagementGroup)
