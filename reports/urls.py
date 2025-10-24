from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report pages
    path('complaints/', views.complaints_report, name='complaints_report'),
    path('invoices/', views.invoice_report, name='invoice_report'),
    path('payments/', views.payment_report, name='payment_report'),
    path('amcs/', views.amc_report, name='amc_report'),
    path('quotations/', views.quotation_report, name='quotation_report'),
    path('routine-services/', views.routine_service_report, name='routine_service_report'),
    
    # Export endpoints - CSV
    path('export/complaints/csv/', views.export_complaints_csv, name='export_complaints_csv'),
    path('export/invoices/csv/', views.export_invoices_csv, name='export_invoices_csv'),
    path('export/quotations/csv/', views.export_quotations_csv, name='export_quotations_csv'),
    path('export/payments/csv/', views.export_payments_csv, name='export_payments_csv'),
    path('export/amc/csv/', views.export_amc_csv, name='export_amc_csv'),
    path('export/routine-services/csv/', views.export_routine_service_csv, name='export_routine_service_csv'),
    
    # Export endpoints - XLSX
    path('export/complaints/xlsx/', views.export_complaints_xlsx, name='export_complaints_xlsx'),
    path('export/invoices/xlsx/', views.export_invoices_xlsx, name='export_invoices_xlsx'),
    path('export/quotations/xlsx/', views.export_quotations_xlsx, name='export_quotations_xlsx'),
    path('export/payments/xlsx/', views.export_payments_xlsx, name='export_payments_xlsx'),
    path('export/amc/xlsx/', views.export_amc_xlsx, name='export_amc_xlsx'),
    path('export/routine-services/xlsx/', views.export_routine_service_xlsx, name='export_routine_service_xlsx'),
]
