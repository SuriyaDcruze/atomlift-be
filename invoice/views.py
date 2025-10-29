# invoice/views.py
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging
import json

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


@csrf_exempt
def add_invoice_custom(request):
    from customer.models import Customer
    from amc.models import AMCType
    from items.models import Item
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            invoice = Invoice.objects.create(
                customer_id=data.get('customer') or None,
                amc_type_id=data.get('amc_type') or None,
                start_date=data.get('start_date'),
                due_date=data.get('due_date'),
                discount=data.get('discount', 0),
                payment_term=data.get('payment_term', 'cash'),
                status=data.get('status', 'open'),
            )

            # ✅ Save invoice items correctly
            for item_data in data.get('items', []):
                if not item_data.get('item'):
                    continue
                InvoiceItem.objects.create(
                    invoice=invoice,
                    item_id=item_data.get('item'),
                    rate=item_data.get('rate', 0),
                    qty=item_data.get('qty', 1),
                    tax=item_data.get('tax', 0),
                )

            return JsonResponse({'success': True, 'message': 'Invoice created successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # GET: render form
    customers = Customer.objects.all()
    amc_types = AMCType.objects.all()
    items = Item.objects.all()
    
    # Get customerId from URL parameter if provided
    customer_id = request.GET.get('customerId', None)
    preselected_customer = None
    if customer_id:
        try:
            preselected_customer = Customer.objects.get(id=customer_id)
        except (Customer.DoesNotExist, ValueError):
            pass

    # Generate preview invoice number for new invoices
    preview_invoice_number = None
    if not request.GET.get('edit'):
        last_invoice = Invoice.objects.all().order_by('id').last()
        if last_invoice and last_invoice.reference_id.startswith(Invoice.REFERENCE_PREFIX):
            last_id = int(last_invoice.reference_id.replace(Invoice.REFERENCE_PREFIX, ''))
        else:
            last_id = 0
        preview_invoice_number = f'{Invoice.REFERENCE_PREFIX}{str(last_id + 1).zfill(3)}'

    return render(request, 'invoice/add_invoice_custom.html', {
        'customers': customers,
        'amc_types': amc_types,
        'items': items,
        'is_edit': False,
        'preselected_customer': preselected_customer,
        'preview_invoice_number': preview_invoice_number
    })


def view_invoice_custom(request, reference_id):
    """Custom invoice detail view"""
    try:
        invoice = Invoice.objects.select_related('customer', 'amc_type').prefetch_related('items__item').get(reference_id=reference_id)
    except Invoice.DoesNotExist:
        messages.error(request, 'Invoice not found')
        return render(request, '404.html')
    
    return render(request, 'invoice/view_invoice_custom.html', {
        'invoice': invoice,
    })


def edit_invoice_custom(request, reference_id):
    """Custom edit invoice page"""
    from customer.models import Customer
    from amc.models import AMCType
    from items.models import Item
    
    try:
        invoice = Invoice.objects.get(reference_id=reference_id)
    except Invoice.DoesNotExist:
        messages.error(request, 'Invoice not found')
        return render(request, '404.html')

    customers = Customer.objects.all()
    amc_types = AMCType.objects.all()
    items = Item.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Update invoice fields
            invoice.customer_id = data.get('customer') if data.get('customer') else None
            invoice.amc_type_id = data.get('amc_type') if data.get('amc_type') else None
            invoice.start_date = data.get('start_date')
            invoice.due_date = data.get('due_date')
            invoice.discount = data.get('discount', 0)
            invoice.payment_term = data.get('payment_term', 'cash')
            invoice.status = data.get('status', 'open')
            if data.get('uploads_files'):
                invoice.uploads_files = data.get('uploads_files')
            invoice.save()



            return JsonResponse({'success': True, 'message': 'Invoice updated successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'invoice/add_invoice_custom.html', {
        'invoice': invoice,
        'customers': customers,
        'amc_types': amc_types,
        'items': items,
        'is_edit': True
    })


# API endpoints for dropdown management
@csrf_exempt
def manage_customers(request):
    """API for managing customers: GET list, POST create"""
    from customer.models import Customer
    
    if request.method == 'GET':
        customers = Customer.objects.all().values('id', 'site_name').order_by('site_name')
        return JsonResponse(list(customers), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            site_name = data.get('site_name', '').strip()
            if not site_name:
                return JsonResponse({"error": "Site name is required"}, status=400)
            if Customer.objects.filter(site_name=site_name).exists():
                return JsonResponse({"error": "Customer already exists"}, status=400)
            customer = Customer.objects.create(site_name=site_name)
            return JsonResponse({
                "success": True,
                "id": customer.id,
                "site_name": customer.site_name
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def manage_amc_types(request):
    """API for managing AMC types: GET list, POST create"""
    from amc.models import AMCType
    
    if request.method == 'GET':
        amc_types = AMCType.objects.all().values('id', 'name').order_by('name')
        return JsonResponse(list(amc_types), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)
            if AMCType.objects.filter(name=name).exists():
                return JsonResponse({"error": "AMC Type already exists"}, status=400)
            amc_type = AMCType.objects.create(name=name)
            return JsonResponse({
                "success": True,
                "id": amc_type.id,
                "name": amc_type.name
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def manage_customers_detail(request, pk):
    """API for updating/deleting customers"""
    from customer.models import Customer
    
    try:
        customer = Customer.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            site_name = data.get('site_name', '').strip()
            if not site_name:
                return JsonResponse({"error": "Site name is required"}, status=400)
            if Customer.objects.filter(site_name=site_name).exclude(pk=pk).exists():
                return JsonResponse({"error": "Customer already exists"}, status=400)
            customer.site_name = site_name
            customer.save()
            return JsonResponse({'success': True, 'message': 'Customer updated'})
        elif request.method == 'DELETE':
            customer.delete()
            return JsonResponse({'success': True, 'message': 'Customer deleted'})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def manage_amc_types_detail(request, pk):
    """API for updating/deleting AMC types"""
    from amc.models import AMCType
    
    try:
        amc_type = AMCType.objects.get(pk=pk)
        if request.method == 'PUT':
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)
            if AMCType.objects.filter(name=name).exclude(pk=pk).exists():
                return JsonResponse({"error": "AMC Type already exists"}, status=400)
            amc_type.name = name
            amc_type.save()
            return JsonResponse({'success': True, 'message': 'AMC Type updated'})
        elif request.method == 'DELETE':
            amc_type.delete()
            return JsonResponse({'success': True, 'message': 'AMC Type deleted'})
    except AMCType.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'AMC Type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def manage_items(request):
    """API for managing items: GET list"""
    from items.models import Item
    
    if request.method == 'GET':
        items = Item.objects.all().values('id', 'name', 'sale_price').order_by('name')
        return JsonResponse(list(items), safe=False)
