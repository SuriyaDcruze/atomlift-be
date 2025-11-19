from django.urls import path
from wagtail.snippets.views.snippets import SnippetViewSet
from .wagtail_hooks import MaterialRequestViewSet
from . import views

app_name = 'material_request'

# Create URL patterns for Material Request
urlpatterns = [
    # Frontend view
    path('frontend/', views.frontend_view, name='material_request_frontend'),

    # Bulk import view
    path('bulk-import/', views.bulk_import_view, name='material_request_bulk_import'),

    # API endpoints for Material Request CRUD operations
    path('api/list/', views.material_request_list, name='material_request_list'),
    path('api/create/', views.material_request_create, name='material_request_create'),
    path('api/<int:pk>/', views.material_request_detail, name='material_request_detail'),
    path('api/<int:pk>/update/', views.material_request_update, name='material_request_update'),
    path('api/<int:pk>/delete/', views.material_request_delete, name='material_request_delete'),

    # Wagtail admin URLs for Material Request snippets (these are handled by the viewset)
]

# Add the snippet viewset URLs
material_request_viewset = MaterialRequestViewSet()
urlpatterns += material_request_viewset.get_urlpatterns()
