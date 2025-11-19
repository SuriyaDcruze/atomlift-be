from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup, IndexView
from wagtail import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem
from wagtail.permissions import ModelPermissionPolicy
from django.urls import reverse
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from .models import MaterialRequest, BulkImportMaterialRequest
from . import views
import json

# Custom permission policy to deny add permission
class NoAddMaterialRequestPermissionPolicy(ModelPermissionPolicy):
    """Custom permission policy that disallows adding new material requests"""
    def user_has_permission(self, user, action):
        if action == "add":
            return False
        return super().user_has_permission(user, action)


# Material Request SnippetViewSet
class MaterialRequestViewSet(SnippetViewSet):
    model = MaterialRequest
    menu_label = "All Material Requests"
    icon = "form"
    menu_order = 100
    inspect_view_enabled = True  # Enable Wagtail default inspect view
    create_view_enabled = False  # Disable manual creation
    edit_view_enabled = True  # Allow editing existing requests
    
    @property
    def permission_policy(self):
        """Use custom permission policy to deny add permission"""
        return NoAddMaterialRequestPermissionPolicy(self.model)
    
    # Standard list display using model fields
    list_display = (
        'id',
        'date',
        'name',
        'item',
        'brand',
        'file',
        'requested_by',
        'added_by',
    )
    
    search_fields = (
        'name',
        'description',
        'item__name',
        'item__item_number',
        'brand',
        'file',
        'requested_by',
        'added_by',
    )
    
    # Filter options
    list_filter = (
        'date',
        'item',
        'requested_by',
        'added_by',
    )
    
    list_display_add_buttons = None  # Remove the add button from list view
    list_per_page = 20  # Pagination
    
    # Enable export for better data management
    list_export = [
        'id',
        'date',
        'name',
        'description',
        'item',
        'brand',
        'file',
        'added_by',
        'requested_by',
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
                    messages.error(request, "You do not have permission to export material requests.")
                    params = request.GET.copy()
                    params.pop("export", None)
                    url = request.path
                    if params:
                        return redirect(f"{url}?{params.urlencode()}")
                    return redirect(url)
            return super().dispatch(request, *args, **kwargs)

    index_view_class = RestrictedIndexView
    
    def get_form_class(self, for_update=False):
        """Override form to make file field not required"""
        from django.forms import ModelForm
        
        class MaterialRequestForm(ModelForm):
            class Meta:
                model = MaterialRequest
                fields = '__all__'
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Make file field not required
                self.fields['file'].required = False
        
        return MaterialRequestForm
    
    def add_view(self, request):
        """Override add view to prevent manual material request creation"""
        messages.error(
            request, 
            "Material Requests cannot be created manually. Please edit an existing material request."
        )
        # Redirect back to the list view using the snippet URL pattern
        return redirect(reverse('snippets:list', args=[self.model._meta.app_label, self.model._meta.model_name]))

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns()
        return urlpatterns

# Custom ViewSet for Bulk Import
class BulkImportViewSet(SnippetViewSet):
    """Custom ViewSet for Bulk Import Material Requests"""
    model = BulkImportMaterialRequest
    menu_label = "Bulk Import"
    icon = "download"
    menu_order = 200
    add_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
    inspect_view_enabled = False
    
    # Override the index view to show bulk import page
    class BulkImportIndexView(IndexView):
        def dispatch(self, request, *args, **kwargs):
            # Redirect to bulk import view instead of showing list
            return views.bulk_import_view(request)
    
    index_view_class = BulkImportIndexView

# Material Request Group
class MaterialRequestGroup(SnippetViewSetGroup):
    items = (
        MaterialRequestViewSet,
        BulkImportViewSet,
    )
    menu_icon = "form"
    menu_label = "Material Request"
    menu_name = "material_request"
    menu_order = 11  # Appears above Travel Request (menu_order = 12)

# Register the Material Request group (appears above Travel Request)
register_snippet(MaterialRequestGroup)

# Hook to remove any add buttons that might appear
@hooks.register('construct_snippet_listing_buttons')
def remove_material_request_add_buttons(buttons, snippet, user, context=None):
    """Remove any add buttons for MaterialRequest"""
    if isinstance(snippet, MaterialRequest):
        # Remove any add/create buttons
        buttons[:] = [btn for btn in buttons if not (
            hasattr(btn, 'label') and ('Add' in str(btn.label) or 'Create' in str(btn.label))
        )]
    return buttons


