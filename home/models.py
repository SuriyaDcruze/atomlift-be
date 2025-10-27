from django.db import models

from wagtail.models import Page
from customer.models import Customer
from complaints.models import Complaint


class HomePage(Page):
    def get_context(self, request):
        context = super().get_context(request)
        context['total_customers'] = Customer.objects.count()
        context['total_complaints'] = Complaint.objects.count()
        context['open_complaints'] = Complaint.objects.filter(status__in=['open', 'in_progress']).count()
        return context
