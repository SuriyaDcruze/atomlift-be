from django.urls import path
from . import views

urlpatterns = [
    # Mobile app API endpoints - User endpoints
    path("api/leave/create/", views.create_leave_request, name="create_leave_request"),
    path("api/leave/list/", views.list_user_leave_requests, name="list_user_leave_requests"),
    path("api/leave/<int:pk>/", views.get_leave_request_detail, name="get_leave_request_detail"),
    path("api/leave/<int:pk>/update/", views.update_user_leave_request, name="update_user_leave_request"),
    path("api/leave/<int:pk>/delete/", views.delete_user_leave_request, name="delete_user_leave_request"),
    path("api/leave/types/", views.get_leave_types, name="get_leave_types"),
    path("api/leave/counts/", views.get_user_leave_counts_api, name="get_user_leave_counts"),
    
    # Admin API endpoints
    path("api/leave/admin/list/", views.list_all_leave_requests, name="list_all_leave_requests"),
    path("api/leave/admin/<int:pk>/update/", views.update_leave_request_status, name="update_leave_request_status"),
]

