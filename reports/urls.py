from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report pages
    path('complaints/', views.complaints_report, name='complaints_report'),
    path('invoices/', views.invoice_report, name='invoice_report'),
    path('payments/', views.payment_report, name='payment_report'),
    path('quotations/', views.quotation_report, name='quotation_report'),
    path('routine-services/', views.routine_service_report, name='routine_service_report'),
    
    # Export endpoints
    path('export/complaints/csv/', views.export_complaints_csv, name='export_complaints_csv'),
    path('export/invoices/csv/', views.export_invoices_csv, name='export_invoices_csv'),
    path('export/quotations/csv/', views.export_quotations_csv, name='export_quotations_csv'),
]
