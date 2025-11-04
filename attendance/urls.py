from django.urls import path
from . import views

urlpatterns = [
    # Mobile app API endpoints - User endpoints
    path("api/attendance/check-in/", views.mark_attendance_in, name="mark_attendance_in"),
    path("api/attendance/work-check-in/", views.work_check_in, name="work_check_in"),
    path("api/attendance/check-out/", views.check_out, name="check_out"),
    path("api/attendance/list/", views.get_user_attendance, name="get_user_attendance"),
    path("api/attendance/today/", views.get_today_attendance, name="get_today_attendance"),
    path("api/attendance/<int:pk>/", views.get_attendance_detail, name="get_attendance_detail"),
    
    # Admin API endpoints
    path("api/attendance/admin/list/", views.list_all_attendance, name="list_all_attendance"),
]

