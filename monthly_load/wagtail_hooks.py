from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from .models import MonthlyLoad

# Create ViewSet for Monthly Load
class MonthlyLoadViewSet(SnippetViewSet):
    model = MonthlyLoad
    menu_label = "Monthly Loads"
    icon = "calendar"
    list_display = ["id"]
    list_filter = []
    search_fields = []

# Create a group for Monthly Load operations
class MonthlyLoadGroup(SnippetViewSetGroup):
    items = (MonthlyLoadViewSet,)
    menu_icon = "calendar"
    menu_label = "Monthly Load"
    menu_name = "monthly_load"
    menu_order = 9

# Register the Monthly Load group
register_snippet(MonthlyLoadGroup)
