from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Existing customer details endpoint
    path("customer/<int:pk>/", views.customer_details, name="customer_details"),

    # API endpoints for fetching dropdown options
    path("api/customer/states/", views.get_states, name="get_states"),
    path("api/customer/routes/", views.get_routes, name="get_routes"),
    path("api/customer/branches/", views.get_branches, name="get_branches"),

    # CRUD operations for states
    path("api/customer/states/", views.create_state, name="create_state"),
    path("api/customer/states/<int:state_id>/", views.update_state, name="update_state"),
    path("api/customer/states/<int:state_id>/delete/", views.delete_state, name="delete_state"),

    # CRUD operations for routes
    path("api/customer/routes/", views.create_route, name="create_route"),
    path("api/customer/routes/<int:route_id>/", views.update_route, name="update_route"),
    path("api/customer/routes/<int:route_id>/delete/", views.delete_route, name="delete_route"),

    # CRUD operations for branches
    path("api/customer/branches/", views.create_branch, name="create_branch"),
    path("api/customer/branches/<int:branch_id>/", views.update_branch, name="update_branch"),
    path("api/customer/branches/<int:branch_id>/delete/", views.delete_branch, name="delete_branch"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
