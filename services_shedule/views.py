from django.shortcuts import render
from django.views.generic import ListView
from .models import ServiceSchedule

# Create your views here.

class ServiceScheduleListView(ListView):
    model = ServiceSchedule
    template_name = 'services_shedule/list.html'
    context_object_name = 'service_schedules'

    def get_queryset(self):
        return ServiceSchedule.objects.all()
