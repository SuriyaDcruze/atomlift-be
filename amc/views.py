# amc/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import logging
import json

from .models import AMCRoutineService, AMCExpiringThisMonth, AMCExpiringLastMonth, AMCExpiringNextMonth, AMC, AMCType
from customer.models import Customer
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import AMCCreateSerializer, AMCListSerializer

logger = logging.getLogger(__name__)


def get_customer_json(request, id):
    """API endpoint to get customer details as JSON"""
    try:
        customer = get_object_or_404(Customer, id=id)
        return JsonResponse({
            'id': customer.id,
            'reference_id': customer.reference_id,
            'site_name': customer.site_name,
            'site_address': customer.site_address,
            'job_no': customer.job_no,
            'latitude': str(customer.latitude) if customer.latitude else None,
            'longitude': str(customer.longitude) if customer.longitude else None,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


def amc_expiring_this_month(request):
    """View for AMCs expiring this month"""
    today = timezone.now().date()
    first_of_month = today.replace(day=1)
    last_day_of_month = (first_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    amcs = AMCExpiringThisMonth.objects.filter(
        end_date__gte=first_of_month,
        end_date__lte=last_day_of_month
    ).select_related('customer').order_by('end_date')
    return render(request, 'amc/amc_expiring_this_month.html', {
        'amcs': amcs,
        'title': 'AMCs Expiring This Month'
    })


def amc_expiring_last_month(request):
    """View for AMCs that expired last month"""
    today = timezone.now().date()
    first_of_month = today.replace(day=1)
    last_month_last_day = first_of_month - timedelta(days=1)
    last_month_first_day = last_month_last_day.replace(day=1)
    amcs = AMCExpiringLastMonth.objects.filter(
        end_date__gte=last_month_first_day,
        end_date__lte=last_month_last_day
    ).select_related('customer').order_by('end_date')
    return render(request, 'amc/amc_expiring_last_month.html', {
        'amcs': amcs,
        'title': 'AMCs Expired Last Month'
    })


def amc_expiring_next_month(request):
    """View for AMCs expiring next month"""
    today = timezone.now().date()
    first_of_month = today.replace(day=1)
    next_month_first = (first_of_month + timedelta(days=32)).replace(day=1)
    next_month_last = (next_month_first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    amcs = AMCExpiringNextMonth.objects.filter(
        end_date__gte=next_month_first,
        end_date__lte=next_month_last
    ).select_related('customer').order_by('end_date')
    return render(request, 'amc/amc_expiring_next_month.html', {
        'amcs': amcs,
        'title': 'AMCs Expiring Next Month'
    })


# Form views (stubs - may need implementation)
def amc_form(request, pk):
    """Form view for AMC"""
    return JsonResponse({'message': 'AMC form view - to be implemented'}, status=501)


def customer_form(request, pk):
    """Form view for customer"""
    return JsonResponse({'message': 'Customer form view - to be implemented'}, status=501)


# API endpoints for AMC types
@require_http_methods(["GET", "POST"])
@csrf_exempt
def amc_types_list(request):
    """API for listing and creating AMC types"""
    if request.method == 'GET':
        amc_types = AMCType.objects.all().values('id', 'name')
        return JsonResponse(list(amc_types), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if hasattr(request, 'body') else request.POST
            amc_type = AMCType.objects.create(name=data['name'])
            return JsonResponse({'id': amc_type.id, 'name': amc_type.name}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["PUT", "DELETE"])
@csrf_exempt
def amc_types_detail(request, amc_type_id):
    """API for updating/deleting AMC types"""
    try:
        amc_type = get_object_or_404(AMCType, id=amc_type_id)
        if request.method == 'PUT':
            data = json.loads(request.body) if hasattr(request, 'body') else request.POST
            amc_type.name = data.get('name', amc_type.name)
            amc_type.save()
            return JsonResponse({'id': amc_type.id, 'name': amc_type.name})
        elif request.method == 'DELETE':
            amc_type.delete()
            return JsonResponse({'message': 'Deleted successfully'}, status=204)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# API endpoints for payment terms (stubs - payment terms may be disabled)
@require_http_methods(["GET", "POST"])
@csrf_exempt
def payment_terms_list(request):
    """API for listing payment terms"""
    return JsonResponse([], safe=False)


@require_http_methods(["PUT", "DELETE"])
@csrf_exempt
def payment_terms_detail(request, payment_term_id):
    """API for payment terms detail"""
    return JsonResponse({'error': 'Payment terms feature is disabled'}, status=400)


# API to get next AMC reference
@require_http_methods(["GET"])
def get_next_amc_reference(request):
    """Get the next AMC reference ID - matches the logic in AMC.save()"""
    try:
        # Use the same logic as AMC.save() method
        last_amc = AMC.objects.order_by("id").last()
        last_id = 0
        if last_amc and last_amc.reference_id and last_amc.reference_id.startswith("AMC"):
            try:
                # Extract number from reference_id (e.g., "AMC03" -> 3)
                last_id = int(last_amc.reference_id.replace("AMC", ""))
            except ValueError:
                last_id = 0
        next_reference = f"AMC{str(last_id + 1).zfill(2)}"
        # Return both for backward compatibility
        return JsonResponse({
            'next_reference': next_reference,
            'reference_id': next_reference
        })
    except Exception as e:
        logger.error(f"Error generating next AMC reference: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# Mobile app API endpoints
@api_view(['GET'])
@csrf_exempt
def list_amcs_mobile(request):
    """Mobile API to list AMCs"""
    try:
        amcs = AMC.objects.select_related('customer', 'amc_type').all()
        serializer = AMCListSerializer(amcs, many=True)
        return Response({'amcs': serializer.data})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def create_amc_mobile(request):
    """Mobile API to create AMC"""
    try:
        serializer = AMCCreateSerializer(data=request.data)
        if serializer.is_valid():
            amc = serializer.save()
            return Response({
                'message': 'AMC created successfully',
                'amc': {
                    'id': amc.id,
                    'reference_id': amc.reference_id,
                    'customer': amc.customer.site_name if amc.customer else None,
                    'start_date': amc.start_date.strftime('%Y-%m-%d') if amc.start_date else None,
                    'end_date': amc.end_date.strftime('%Y-%m-%d') if amc.end_date else None,
                    'status': amc.status
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@csrf_exempt
def list_amc_types_mobile(request):
    """Mobile API to list AMC types"""
    try:
        amc_types = AMCType.objects.all().values('id', 'name')
        return Response({'amc_types': list(amc_types)})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def create_amc_type_mobile(request):
    """Mobile API to create AMC type"""
    try:
        name = request.data.get('name')
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        amc_type = AMCType.objects.create(name=name)
        return Response({
            'message': 'AMC type created successfully',
            'amc_type': {'id': amc_type.id, 'name': amc_type.name}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def print_routine_service_certificate(request, pk):
    """Generate and download a PDF certificate for a routine service visit"""
    try:
        service = get_object_or_404(
            AMCRoutineService.objects.select_related('amc__customer', 'employee_assign'),
            pk=pk
        )
        
        amc = service.amc
        customer = amc.customer
        
        # Prepare context data (matching complaint PDF format)
        context = {
            'company_name': 'Atom Lifts India Pvt Ltd',
            'address': 'No.87B, Pillayar Koil Street, Mannurpet, Ambattur Indus Estate, Chennai 50., CHENNAI',
            'phone': '9600087456',
            'email': 'admin@atomlifts.com',
            'amc_no': amc.reference_id if amc else 'N/A',
            'service_date': service.service_date.strftime('%d/%m/%Y'),
            'service_month': service.service_date.strftime('%B'),
            'site_name': customer.site_name if customer else 'N/A',
            'site_address': customer.site_address if customer and customer.site_address else 'N/A',
            'assign_to': (
                f"{service.employee_assign.first_name} {service.employee_assign.last_name}".strip()
                or service.employee_assign.username
                if service.employee_assign else "Unassigned"
            ),
            'technician_remark': '',
            'service_provided': '',
            'customer_remark': '',
            'service': '',
            'attend_date_time': '',
            'service_status': service.get_status_display() if service.status != 'due' else 'Due',
        }
        
        # Build PDF (matching complaint PDF format)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []
        
        # Header (matching complaint format)
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
        
        # Certificate Title
        story.append(Paragraph("CERTIFICATE OF ROUTINE SERVICE VISIT", header_style))
        story.append(Spacer(1, 12))
        
        # Service Information (matching complaint format)
        data = [
            ['AMC No.:', context['amc_no']],
            ['Service Date:', context['service_date']],
            ['Service Month:', context['service_month']],
        ]
        table = Table(data, colWidths=[100, 400])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Customer Information (matching complaint format)
        story.append(Paragraph("Customer Information", styles['Heading2']))
        cust_data = [
            ['Site Name:', context['site_name']],
            ['Site Address:', context['site_address']],
            ['Note:', ''],
        ]
        cust_table = Table(cust_data, colWidths=[100, 400])
        cust_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(cust_table)
        story.append(Spacer(1, 12))
        
        # Service Details (matching complaint format)
        story.append(Paragraph("Service Details", styles['Heading2']))
        story.append(Paragraph(f"Assign To: {context['assign_to']}", styles['Normal']))
        story.append(Paragraph(f"Technician Remark: {context['technician_remark']}", styles['Normal']))
        story.append(Paragraph(f"Service Provided: {context['service_provided']}", styles['Normal']))
        story.append(Paragraph(f"Customer Remark: {context['customer_remark']}", styles['Normal']))
        story.append(Paragraph(f"Service: {context['service']}", styles['Normal']))
        story.append(Paragraph(f"Attend Date & Time: {context['attend_date_time']}", styles['Normal']))
        story.append(Paragraph(f"Service Status: {context['service_status']}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Signatures (matching complaint format)
        story.append(Paragraph("Signatures", styles['Heading2']))
        
        # Customer Signature
        story.append(Paragraph("Customer Signature:", styles['Normal']))
        story.append(Paragraph("___________________________", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Technician Signature
        story.append(Paragraph("Technician Signature:", styles['Normal']))
        story.append(Paragraph("___________________________", styles['Normal']))
        story.append(Spacer(1, 12))
        
        story.append(Spacer(1, 12))
        
        # Build and return
        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f'Routine_Service_Certificate_{context["amc_no"]}_{service.service_date.strftime("%Y%m%d")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Error generating routine service certificate PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
