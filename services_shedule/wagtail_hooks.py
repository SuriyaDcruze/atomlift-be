from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from .models import RoutineServiceScheduleView

# Custom permission policy to deny add permission
from wagtail.permissions import ModelPermissionPolicy

class NoAddRoutineServiceSchedulePermissionPolicy(ModelPermissionPolicy):
    """Custom permission policy that disallows adding new routine service schedules"""
    def user_has_permission(self, user, action):
        if action == "add":
            return False
        return super().user_has_permission(user, action)

# Create ViewSet for Service Schedule
class RoutineServiceScheduleViewSet(SnippetViewSet):
    model = RoutineServiceScheduleView
    menu_label = "Routine Service Schedule"
    menu_icon = "date"
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add permission"""
        return NoAddRoutineServiceSchedulePermissionPolicy(self.model)

    list_display = [
        "site_name_display",
        "route_display",
        "amc_display",
        "status",
        "scheduled_services_count",
        "contract_start_display",
        "contract_end_display",
        "contract_type_display",
        "service_1",
        "service_2",
        "service_3",
        "service_4",
        "service_5",
        "service_6",
        "service_7",
        "service_8",
        "service_9",
        "service_10",
        "service_11",
        "service_12",
    ]
    list_filter = ["status", "amc_type", "customer__city"]
    search_fields = ["reference_id", "customer__site_name"]

    list_export = [
        "site_name_display",
        "route_display",
        "amc_display",
        "status",
        "scheduled_services_count",
        "contract_start_display",
        "contract_end_display",
        "contract_type_display",
        "service_1",
        "service_2",
        "service_3",
        "service_4",
        "service_5",
        "service_6",
        "service_7",
        "service_8",
        "service_9",
        "service_10",
        "service_11",
        "service_12",
    ]
    export_formats = ["csv", "xlsx"]

    # Custom IndexView to restrict export to superusers
    class RestrictedIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            """Override dispatch to check export permissions"""
            export_format = request.GET.get('export')
            if export_format in ['csv', 'xlsx']:
                if not request.user.is_superuser:
                    from django.contrib import messages
                    from django.shortcuts import redirect
                    messages.error(request, "You do not have permission to export service schedules.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)

    index_view_class = RestrictedIndexView

    def get_queryset(self, request):
        """
        Override to filter AMCs that have at least one routine service scheduled.
        """
        return self.model.objects.filter(routine_services__isnull=False).distinct()
    
    # Disable add/edit/delete from this view as it's a view-only schedule
    add_view_enabled = False
    create_view_enabled = False # Explicitly disable create view
    edit_view_enabled = False
    delete_view_enabled = False
    inspect_view_enabled = True

# Create a group for Service Schedule operations
class ServiceScheduleGroup(SnippetViewSetGroup):
    items = (RoutineServiceScheduleViewSet,)
    menu_icon = "date"
    menu_label = "Service Schedule"
    menu_name = "service_schedule"
    menu_order = 10

# Register the Service Schedule group
register_snippet(ServiceScheduleGroup)

from wagtail import hooks
from django.utils.html import format_html
from django.templatetags.static import static

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('services_shedule/css/service_schedule.css'))
