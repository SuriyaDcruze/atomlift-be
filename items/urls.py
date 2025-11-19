# urls.py (corrected to remove custom add/edit paths since moved to wagtail_hooks, updated to match new view functions)
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # API endpoints for dropdown management
    path('api/types/', views.manage_types, name='api_manage_types'),
    path('api/types/<int:pk>/', views.manage_types_detail, name='api_manage_types_detail'),
    path('api/makes/', views.manage_makes, name='api_manage_makes'),
    path('api/makes/<int:pk>/', views.manage_makes_detail, name='api_manage_makes_detail'),
    path('api/units/', views.manage_units, name='api_manage_units'),
    path('api/units/<int:pk>/', views.manage_units_detail, name='api_manage_units_detail'),

    # API endpoint for items list
    path('api/items/', views.manage_items, name='api_manage_items'),

    # Bulk import view
    path('bulk-import/', views.bulk_import_view, name='item_bulk_import'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
