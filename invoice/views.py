# invoice/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging

from .models import Invoice, InvoiceItem

logger = logging.getLogger(__name__)


def download_invoice_pdf(request, pk):
    """Generate and download a PDF for a specific invoice."""
    try:
        invoice = get_object_or_404(
            Invoice.objects.select_related('customer', 'amc_type').prefetch_related('items__item'),
            pk=pk
        )

        # --- Context Preparation ---
        context = {
            'company_name': 'Atom Lifts India Pvt Ltd',
            'address': 'No.87B, Pillayar Koll Street, Mannurpet, Ambattur Indus Estate, Chennai 50',
            'phone': '9600087456',
            'email': 'admin@atomlifts.com',

            'invoice_no': invoice.reference_id,
            'invoice_date': invoice.start_date.strftime('%d/%m/%Y') if invoice.start_date else '',
            'due_date': invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else '',
            'customer_name': getattr(invoice.customer, 'site_name', '') if invoice.customer else '',
            'customer_address': getattr(invoice.customer, 'site_address', '') if invoice.customer else '',
            'amc_type': getattr(invoice.amc_type, 'name', '') if invoice.amc_type else '',
            'discount': f"{invoice.discount}%",
            'payment_term': invoice.get_payment_term_display(),
            'status': invoice.get_status_display(),
        }

        # --- Build PDF ---
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []

        # Header
        header_style = ParagraphStyle(name='HeaderStyle', parent=styles['Heading1'], fontSize=18, alignment=1)
        story.append(Paragraph(context['company_name'], header_style))
        story.append(Paragraph(context['address'], styles['Normal']))
        story.append(Paragraph(f"Phone: {context['phone']} | Email: {context['email']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Invoice Summary
        data = [
            ['Invoice No:', context['invoice_no']],
            ['Invoice Date:', context['invoice_date']],
            ['Due Date:', context['due_date']],
            ['AMC Type:', context['amc_type']],
            ['Status:', context['status']],
        ]
        summary_table = Table(data, colWidths=[100, 400])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # Customer Info
        story.append(Paragraph("Customer Details", styles['Heading2']))
        cust_data = [
            ['Customer Name:', context['customer_name']],
            ['Address:', context['customer_address']],
            ['Payment Term:', context['payment_term']],
            ['Discount:', context['discount']],
        ]
        cust_table = Table(cust_data, colWidths=[100, 400])
        cust_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(cust_table)
        story.append(Spacer(1, 12))

        # Invoice Items
        story.append(Paragraph("Invoice Items", styles['Heading2']))
        item_data = [['Item', 'Rate', 'Qty', 'Tax (%)', 'Total']]
        for item in invoice.items.all():
            item_data.append([
                getattr(item.item, 'name', 'N/A'),
                f"{item.rate:.2f}",
                str(item.qty),
                f"{item.tax:.2f}",
                f"{item.total:.2f}",
            ])
        item_table = Table(item_data, colWidths=[180, 80, 60, 80, 100])
        item_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 12))

        # Totals
        grand_total = sum(item.total for item in invoice.items.all())
        story.append(Paragraph(f"<b>Grand Total:</b> ₹{grand_total:.2f}", styles['Heading3']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=invoice_{context["invoice_no"]}.pdf'
        return response

    except Exception as e:
        logger.error(f"Error generating invoice PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
