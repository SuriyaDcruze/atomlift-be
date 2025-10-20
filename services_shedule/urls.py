from django.urls import path
from .views import ServiceScheduleListView

app_name = 'services_shedule'

urlpatterns = [
    path('', ServiceScheduleListView.as_view(), name='service_schedule_list'),
]
