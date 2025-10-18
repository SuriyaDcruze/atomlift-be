from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .models import Customer

def customer_details(request, pk):
    try:
        c = Customer.objects.get(pk=pk)
        return JsonResponse({
            "site_address": c.site_address,
            "job_no": c.job_no,
        })
    except Customer.DoesNotExist:
        return JsonResponse({}, status=404)
