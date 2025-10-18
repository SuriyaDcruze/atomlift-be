# complaints/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging

from .models import Complaint

logger = logging.getLogger(__name__)

def download_complaint_pdf(request, pk):
    """
    Generate and download a PDF for a specific complaint.
    Accessible via Wagtail admin custom button.
    """
    try:
        complaint = get_object_or_404(
            Complaint.objects.select_related('customer', 'assign_to', 'complaint_type', 'priority'),
            pk=pk
        )

        # --- Prepare data ---
        context = {
            'company_name': 'Atom Lifts India Pvt Ltd',
            'address': 'No.87B, Pillayar Koll Street, Mannurpet, Ambattur Indus Estate, Chennai 50, CHENNAI',
            'phone': '9600087456',
            'email': 'admin@atomlifts.com',
            'ticket_no': complaint.reference or '',
            'ticket_date': complaint.date.strftime('%d/%m/%Y') if complaint.date else '',
            'ticket_type': complaint.complaint_type.name if complaint.complaint_type else '',
            'priority': complaint.priority.name if complaint.priority else '',
            'customer_name': getattr(complaint.customer, 'site_name', '') if complaint.customer else '',
            'site_address': getattr(complaint.customer, 'site_address', '') if complaint.customer else '',
            'contact_person': getattr(complaint.customer, 'contact_person_name', '') or complaint.contact_person_name or '',
            'contact_mobile': getattr(complaint.customer, 'phone', '') or complaint.contact_person_mobile or '',
            'block_wing': complaint.block_wing or '',
            'subject': complaint.subject or '',
            'message': complaint.message or '',
             'assigned_to': (
        f"{complaint.assign_to.first_name} {complaint.assign_to.last_name}".strip()
        or complaint.assign_to.username
        if complaint.assign_to else "Unassigned"
    ),
            'technician_remark': complaint.technician_remark or '',
            'solution': complaint.solution or '',
        }

        # --- Create PDF ---
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []

        # Header
        header_style = ParagraphStyle(
            name='HeaderStyle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=1  # Center
        )
        story.append(Paragraph(context['company_name'], header_style))
        story.append(Paragraph(context['address'], styles['Normal']))
        story.append(Paragraph(f"Phone: {context['phone']} | Email: {context['email']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Complaint Info
        data = [
            ['Ticket No:', context['ticket_no']],
            ['Date:', context['ticket_date']],
            ['Type:', context['ticket_type']],
            ['Priority:', context['priority']],
        ]
        table = Table(data, colWidths=[100, 400])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        # Customer Details
        story.append(Paragraph("Customer Details", styles['Heading2']))
        cust_data = [
            ['Customer Name:', context['customer_name']],
            ['Site Address:', context['site_address']],
            ['Contact Person:', context['contact_person']],
            ['Contact Mobile:', context['contact_mobile']],
            ['Block/Wing:', context['block_wing']],
        ]
        cust_table = Table(cust_data, colWidths=[100, 400])
        cust_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(cust_table)
        story.append(Spacer(1, 12))

        # Complaint Details
        story.append(Paragraph("Complaint Details", styles['Heading2']))
        story.append(Paragraph(f"Subject: {context['subject']}", styles['Normal']))
        story.append(Paragraph(f"Message: {context['message']}", styles['Normal']))
        story.append(Paragraph(f"Assigned To: {context['assigned_to']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Resolution
        story.append(Paragraph("Resolution", styles['Heading2']))
        story.append(Paragraph(f"Technician Remark: {context['technician_remark']}", styles['Normal']))
        story.append(Paragraph(f"Solution: {context['solution']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Build and return
        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=complaint_{context["ticket_no"] or complaint.pk}.pdf'
        return response

    except Exception as e:
        logger.error(f"Error generating complaint PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
