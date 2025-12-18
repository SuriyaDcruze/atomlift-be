from django.urls import path
from . import views

app_name = 'routine_services'

urlpatterns = [
    path('', views.routine_services, name='routine_services'),
    path('today/', views.today_routine_services, name='today_routine_services'),
    path('route-wise/', views.route_wise_services, name='route_wise_services'),
    path('this-month/', views.this_month_services, name='this_month_services'),
    path('last-month-overdue/', views.last_month_overdue, name='last_month_overdue'),
    path('this-month-overdue/', views.this_month_overdue, name='this_month_overdue'),
    path('this-month-completed/', views.this_month_completed, name='this_month_completed'),
    path('last-month-completed/', views.last_month_completed, name='last_month_completed'),
    path('pending/', views.pending_services, name='pending_services'),
    
    # Customer mobile app API
    path('api/mobile/routine-services/', views.customer_routine_services, name='customer_routine_services'),
    path('api/mobile/routine-services/all/', views.customer_all_routine_services, name='customer_all_routine_services'),
    path('api/mobile/download-service-slip/', views.download_service_slip, name='download_service_slip'),
]
