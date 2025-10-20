from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from .models import ServiceSchedule

# Create ViewSet for Service Schedule
class ServiceScheduleViewSet(SnippetViewSet):
    model = ServiceSchedule
    menu_label = "Service Schedules"
    menu_icon = "date"
    list_display = ["id"]
    list_filter = []
    search_fields = []

# Create a group for Service Schedule operations
class ServiceScheduleGroup(SnippetViewSetGroup):
    items = (ServiceScheduleViewSet,)
    menu_icon = "date"
    menu_label = "Service Schedule"
    menu_name = "service_schedule"
    menu_order = 8

# Register the Service Schedule group
register_snippet(ServiceScheduleGroup)
