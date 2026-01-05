from django.urls import path
from . import views

urlpatterns = [
    # Sub-customer CRUD operations
    path('api/create/', views.create_subcustomer, name='create_subcustomer'),
    path('api/list/', views.list_subcustomers, name='list_subcustomers'),
    path('api/<int:subcustomer_id>/', views.subcustomer_detail, name='subcustomer_detail'),
    path('api/<int:subcustomer_id>/update/', views.update_subcustomer, name='update_subcustomer'),
    path('api/<int:subcustomer_id>/delete/', views.delete_subcustomer, name='delete_subcustomer'),
    
    # Sub-customer login
    path('api/login/', views.subcustomer_login, name='subcustomer_login'),
]

