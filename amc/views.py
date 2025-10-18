from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import AMC
import json

# Create your views here.

def amc_form(request, pk=None):
    """View for AMC form page"""
    context = {
        'is_edit': pk is not None,
        'amc_id': pk,
    }
    return render(request, 'amc/amc_form.html', context)

def customer_form(request, pk=None):
    """View for Customer form page"""
    context = {
        'is_edit': pk is not None,
        'customer_id': pk,
    }
