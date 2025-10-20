from django.urls import path
from . import views

urlpatterns = [
    # Custom add/edit pages
    path('add-custom/', views.add_requisition_custom, name='add_requisition_custom'),
    path('edit-custom/<str:reference_id>/', views.edit_requisition_custom, name='edit_requisition_custom'),
]





