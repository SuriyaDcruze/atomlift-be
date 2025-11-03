from django.urls import path
from . import views

app_name = 'travelling'

urlpatterns = [
    # API endpoints for travel requests
    path('api/list/', views.travel_request_list, name='travel_request_list'),
    path('api/create/', views.travel_request_create, name='travel_request_create'),
    path('api/<int:pk>/', views.travel_request_detail, name='travel_request_detail'),
    path('api/<int:pk>/update/', views.travel_request_update, name='travel_request_update'),
    path('api/<int:pk>/delete/', views.travel_request_delete, name='travel_request_delete'),
]
