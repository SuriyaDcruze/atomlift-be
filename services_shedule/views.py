from django.shortcuts import render
from django.views.generic import ListView
from .models import RoutineServiceScheduleView

# Create your views here.

class ServiceScheduleListView(ListView):
    model = RoutineServiceScheduleView
    template_name = 'services_shedule/list.html'
    context_object_name = 'service_schedules'

    def get_queryset(self):
        return RoutineServiceScheduleView.objects.all()
