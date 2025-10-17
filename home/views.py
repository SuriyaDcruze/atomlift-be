from django.shortcuts import render
from customer.models import Customer
from complaints.models import Complaint

def lionsol_homepage(request):
    """View for the Lionsol homepage"""
    total_customers = Customer.objects.count()
    total_complaints = Complaint.objects.count()
    open_complaints = Complaint.objects.filter(solution__isnull=True).count()  # Assuming open means no solution

    context = {
        'total_customers': total_customers,
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
    }
    return render(request, 'home/lionsol_homepage.html', context)
