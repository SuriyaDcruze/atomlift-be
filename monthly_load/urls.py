from django.urls import path
from .views import MonthlyLoadListView

app_name = 'monthly_load'

urlpatterns = [
    path('', MonthlyLoadListView.as_view(), name='monthly_load_list'),
]
