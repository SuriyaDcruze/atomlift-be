from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom add/edit pages
    path('add-custom/', views.add_lift_custom, name='add_lift_custom'),
    path('add-custom/<str:job_no>/', views.add_lift_custom, name='add_lift_custom_with_job'),
    path('edit-custom/<str:identifier>/', views.edit_lift_custom, name='edit_lift_custom'),
    
    # Bulk import view
    path('bulk-import/', views.bulk_import_view, name='lift_bulk_import'),
    
    # API endpoints for dropdown management
    path('api/lift/floorids/', views.manage_floorids, name='api_manage_floorids'),
    path('api/lift/floorids/<int:pk>/', views.manage_floorids_detail, name='api_manage_floorids_detail'),
    path('api/lift/brands/', views.manage_brands, name='api_manage_brands'),
    path('api/lift/brands/<int:pk>/', views.manage_brands_detail, name='api_manage_brands_detail'),
    path('api/lift/lifttypes/', views.manage_lifttypes, name='api_manage_lifttypes'),
    path('api/lift/lifttypes/<int:pk>/', views.manage_lifttypes_detail, name='api_manage_lifttypes_detail'),
    path('api/lift/machinetypes/', views.manage_machinetypes, name='api_manage_machinetypes'),
    path('api/lift/machinetypes/<int:pk>/', views.manage_machinetypes_detail, name='api_manage_machinetypes_detail'),
    path('api/lift/machinebrands/', views.manage_machinebrands, name='api_manage_machinebrands'),
    path('api/lift/machinebrands/<int:pk>/', views.manage_machinebrands_detail, name='api_manage_machinebrands_detail'),
    path('api/lift/doortypes/', views.manage_doortypes, name='api_manage_doortypes'),
    path('api/lift/doortypes/<int:pk>/', views.manage_doortypes_detail, name='api_manage_doortypes_detail'),
    path('api/lift/doorbrands/', views.manage_doorbrands, name='api_manage_doorbrands'),
    path('api/lift/doorbrands/<int:pk>/', views.manage_doorbrands_detail, name='api_manage_doorbrands_detail'),
    path('api/lift/controllerbrands/', views.manage_controllerbrands, name='api_manage_controllerbrands'),
    path('api/lift/controllerbrands/<int:pk>/', views.manage_controllerbrands_detail, name='api_manage_controllerbrands_detail'),
    path('api/lift/cabins/', views.manage_cabins, name='api_manage_cabins'),
    path('api/lift/cabins/<int:pk>/', views.manage_cabins_detail, name='api_manage_cabins_detail'),
    path('api/lift/next-reference/', views.get_next_lift_reference, name='api_next_lift_reference'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)