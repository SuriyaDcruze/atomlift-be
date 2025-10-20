from django.shortcuts import render
from django.views.generic import ListView
from .models import MonthlyLoad

# Create your views here.

class MonthlyLoadListView(ListView):
    model = MonthlyLoad
    template_name = 'monthly_load/list.html'
    context_object_name = 'monthly_loads'

    def get_queryset(self):
        return MonthlyLoad.objects.all()
