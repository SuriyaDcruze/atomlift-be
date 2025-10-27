from django.shortcuts import render
from customer.models import Customer
from complaints.models import Complaint

def lionsol_homepage(request):
    """View for the Lionsol homepage"""
    total_customers = Customer.objects.count()
    total_complaints = Complaint.objects.count()
    open_complaints = Complaint.objects.filter(status__in=['open', 'in_progress']).count()

    context = {
        'total_customers': total_customers,
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
    }
    return render(request, 'home/lionsol_homepage.html', context)

def custom_dashboard(request):
    """View for the custom dashboard"""
    return render(request, 'custom_dashboard.html')