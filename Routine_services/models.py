from django.db import models
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, date
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
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
        return RoutineService.objects.all().order_by("-service_date")


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
        "assigned_technician",
        "lift",
    )

    def get_queryset(self, request):
        today = timezone.now().date()
        return RoutineService.objects.filter(service_date=today).order_by("service_date")
    
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
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return RoutineService.objects.filter(
            service_date__gte=start_of_month.date()
        ).order_by("service_date")
    
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
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
        return RoutineService.objects.filter(
            service_date__gte=start_of_last_month.date(),
            service_date__lt=start_of_month.date(),
            status__in=['pending', 'overdue']
        ).order_by("service_date")
    
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
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return RoutineService.objects.filter(
            service_date__gte=start_of_month.date(),
            service_date__lt=today.date(),
            status__in=['pending', 'overdue']
        ).order_by("service_date")
    
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
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return RoutineService.objects.filter(
            service_date__gte=start_of_month.date(),
            status='completed'
        ).order_by("service_date")
    
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
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
        return RoutineService.objects.filter(
            service_date__gte=start_of_last_month.date(),
            service_date__lt=start_of_month.date(),
            status='completed'
        ).order_by("service_date")
    
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
        "customer",
        "service_type",
        "service_date",
        "assigned_technician",
        "lift",
        "customer__city",
    )

    def get_queryset(self, request):
        return RoutineService.objects.filter(status='pending').order_by("service_date")
    
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
