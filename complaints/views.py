# complaints/views.py
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import qrcode
import base64
import logging
import re
from io import BytesIO
try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None

from .models import Complaint, ComplaintType, ComplaintPriority
from customer.models import Customer
from authentication.models import CustomUser

logger = logging.getLogger(__name__)

def svg_to_png_base64(svg_string, width=300, height=100):
    """
    Convert SVG string to PNG base64 for PDF embedding.
    This is a basic implementation - in production, use proper SVG libraries.
    """
    if not svg_string or not svg_string.startswith('<svg'):
        return None

    try:
        if Image is None or ImageDraw is None:
            # Fallback: return None if PIL not available
            return None

        # Create a white background image
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        # Parse SVG paths (very basic parsing)
        # Extract path data from SVG
        path_matches = re.findall(r'd="([^"]*)"', svg_string)

        # Draw black lines for each path
        for path_data in path_matches:
            # Very basic path parsing - only handles M and L commands
            coords = []
            parts = path_data.split()
            i = 0
            while i < len(parts):
                if parts[i].upper() == 'M' and i + 1 < len(parts):
                    # Move to command
                    try:
                        x, y = map(float, parts[i + 1].split(','))
                        coords.append((x, y))
                        i += 2
                    except:
                        i += 1
                elif parts[i].upper() == 'L' and i + 1 < len(parts):
                    # Line to command
                    try:
                        x, y = map(float, parts[i + 1].split(','))
                        coords.append((x, y))
                        i += 2
                    except:
                        i += 1
                else:
                    i += 1

            # Draw lines connecting coordinates
            if len(coords) > 1:
                # Scale coordinates to fit image (assuming original SVG was 300x100)
                scaled_coords = [(x, y) for x, y in coords]
                if len(scaled_coords) > 1:
                    draw.line(scaled_coords, fill='black', width=2)

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f'data:image/png;base64,{img_base64}'

    except Exception as e:
        logger.error(f"Error converting SVG to PNG: {str(e)}")
        return None

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
            'technician_signature': complaint.technician_signature.url if complaint.technician_signature else '',
            'customer_signature': complaint.customer_signature.url if complaint.customer_signature else '',
            'technician_signature_file': complaint.technician_signature if complaint.technician_signature else None,
            'customer_signature_file': complaint.customer_signature if complaint.customer_signature else None,
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

        # Signatures
        story.append(Paragraph("Signatures", styles['Heading2']))

        # Technician Signature
        story.append(Paragraph("Technician Signature:", styles['Normal']))
        if context.get('technician_signature_file'):
            try:
                # Use image file directly - Django ImageField
                sig_file = context['technician_signature_file']
                if hasattr(sig_file, 'path'):
                    # ImageField has a path attribute
                    with open(sig_file.path, 'rb') as f:
                        img_buffer = BytesIO(f.read())
                elif hasattr(sig_file, 'read'):
                    # File object
                    img_buffer = BytesIO(sig_file.read())
                    sig_file.seek(0)  # Reset file pointer
                else:
                    # Fallback: try to open as file path string
                    with open(sig_file, 'rb') as f:
                        img_buffer = BytesIO(f.read())
                sig_img = Image(img_buffer, width=200, height=60)
                story.append(sig_img)
            except Exception as e:
                logger.error(f"Error embedding technician signature image: {str(e)}")
                story.append(Paragraph("[Signature captured digitally]", styles['Italic']))
        else:
            story.append(Paragraph("___________________________", styles['Normal']))
        story.append(Spacer(1, 12))

        # Customer Signature
        story.append(Paragraph("Customer Signature:", styles['Normal']))
        if context.get('customer_signature_file'):
            try:
                # Use image file directly - Django ImageField
                sig_file = context['customer_signature_file']
                if hasattr(sig_file, 'path'):
                    # ImageField has a path attribute
                    with open(sig_file.path, 'rb') as f:
                        img_buffer = BytesIO(f.read())
                elif hasattr(sig_file, 'read'):
                    # File object
                    img_buffer = BytesIO(sig_file.read())
                    sig_file.seek(0)  # Reset file pointer
                else:
                    # Fallback: try to open as file path string
                    with open(sig_file, 'rb') as f:
                        img_buffer = BytesIO(f.read())
                sig_img = Image(img_buffer, width=200, height=60)
                story.append(sig_img)
            except Exception as e:
                logger.error(f"Error embedding customer signature image: {str(e)}")
                story.append(Paragraph("[Signature captured digitally]", styles['Italic']))
        else:
            story.append(Paragraph("___________________________", styles['Normal']))
        story.append(Spacer(1, 12))

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


def add_complaint_custom(request):
    context = {
        'is_edit': False,
    }
    return render(request, 'complaints/add_complaint_custom.html', context)


def edit_complaint_custom(request, reference):
    complaint = get_object_or_404(Complaint, reference=reference)
    context = {
        'is_edit': True,
        'complaint': complaint,
    }
    return render(request, 'complaints/edit_complaint_custom.html', context)


def view_complaint_custom(request, reference):
    """View complaint details page"""
    complaint = get_object_or_404(Complaint, reference=reference)
    
    # Get related complaints from the same customer
    related_complaints = None
    if complaint.customer:
        related_complaints = Complaint.objects.filter(
            customer=complaint.customer
        ).exclude(id=complaint.id).order_by('-date', '-id')
    
    # Get assignment history
    assignment_history = complaint.assignment_history.all().order_by('-assignment_date')
    
    # Get call update history
    call_update_history = complaint.call_update_history.all().order_by('-call_update_date')
    
    context = {
        'complaint': complaint,
        'related_complaints': related_complaints,
        'assignment_history': assignment_history,
        'call_update_history': call_update_history,
    }
    return render(request, 'complaints/view_complaint_custom.html', context)


@require_http_methods(["GET"])
def get_customers(request):
    customers = Customer.objects.all().order_by('site_name')
    data = [{
        'id': c.id,
        'reference_id': c.reference_id,
        'site_name': c.site_name,
        'site_address': c.site_address,
        'contact_person_name': c.contact_person_name,
        'phone': c.phone,
        'mobile': c.mobile,
        'email': c.email,
        'job_no': c.job_no,
        'site_id': c.site_id,
    } for c in customers]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_complaint_types(request):
    types = ComplaintType.objects.all().order_by('name')
    return JsonResponse([{'id': t.id, 'name': t.name} for t in types], safe=False)


@require_http_methods(["GET"])
def get_priorities(request):
    priorities = ComplaintPriority.objects.all().order_by('name')
    return JsonResponse([{'id': p.id, 'name': p.name} for p in priorities], safe=False)


# --- Quick create/update/delete for ComplaintType and ComplaintPriority ("+" icon support) ---

@csrf_exempt
@require_http_methods(["POST"])  # Create Type
def create_complaint_type(request):
    try:
        import json as _json
        payload = request.POST or request.body
        if not isinstance(payload, dict):
            payload = _json.loads(request.body or '{}')
        name = (payload.get('value') or payload.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
        obj, created = ComplaintType.objects.get_or_create(name=name)
        return JsonResponse({'success': True, 'id': obj.id, 'value': obj.name, 'created': created})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])  # Update Type
def update_complaint_type(request, pk):
    try:
        import json as _json
        payload = _json.loads(request.body or '{}')
        name = (payload.get('value') or payload.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
        obj = get_object_or_404(ComplaintType, pk=pk)
        obj.name = name
        obj.save()
        return JsonResponse({'success': True, 'id': obj.id, 'value': obj.name})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])  # Delete Type
def delete_complaint_type(request, pk):
    try:
        obj = get_object_or_404(ComplaintType, pk=pk)
        obj.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])  # Create Priority
def create_complaint_priority(request):
    try:
        import json as _json
        payload = request.POST or request.body
        if not isinstance(payload, dict):
            payload = _json.loads(request.body or '{}')
        name = (payload.get('value') or payload.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
        obj, created = ComplaintPriority.objects.get_or_create(name=name)
        return JsonResponse({'success': True, 'id': obj.id, 'value': obj.name, 'created': created})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])  # Update Priority
def update_complaint_priority(request, pk):
    try:
        import json as _json
        payload = _json.loads(request.body or '{}')
        name = (payload.get('value') or payload.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
        obj = get_object_or_404(ComplaintPriority, pk=pk)
        obj.name = name
        obj.save()
        return JsonResponse({'success': True, 'id': obj.id, 'value': obj.name})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])  # Delete Priority
def delete_complaint_priority(request, pk):
    try:
        obj = get_object_or_404(ComplaintPriority, pk=pk)
        obj.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_executives(request):
    users = CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name')
    return JsonResponse([
        {
            'id': u.id,
            'full_name': f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        } for u in users
    ], safe=False)


@require_http_methods(["GET"])
def get_next_complaint_reference(request):
    last = Complaint.objects.order_by('id').last()
    last_id = 1000
    if last and last.reference and last.reference.startswith('CMP'):
        try:
            last_id = int(last.reference.replace('CMP', ''))
        except ValueError:
            last_id = 1000
    return JsonResponse({'reference': f'CMP{last_id + 1}'})


@require_http_methods(["GET"])
def get_assigned_complaints(request):
    """
    Get complaints assigned to the authenticated user
    Requires token authentication
    """
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Authentication required'}, status=401)

        token_key = auth_header.split(' ')[1]
        from rest_framework.authtoken.models import Token
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # Check if user is in employee group
        if not user.groups.exists():
            return JsonResponse({'error': 'Access denied. Only employees can view assigned complaints'}, status=403)

        # Get complaints assigned to this user
        complaints = Complaint.objects.filter(
            assign_to=user
        ).select_related(
            'customer', 'complaint_type', 'priority', 'assign_to'
        ).order_by('-date', '-id')

        # Format complaints for mobile app
        complaints_data = []
        for complaint in complaints:
            complaints_data.append({
                'id': complaint.id,
                'reference': complaint.reference,
                'title': f"{complaint.customer.site_name} - {complaint.contact_person_name or 'N/A'}",
                'dateTime': complaint.date.strftime('%d %b, %Y %H:%M:%S') if complaint.date else '',
                'status': complaint.status,
                'ticketId': complaint.reference,
                'amcType': complaint.complaint_type.name if complaint.complaint_type else 'N/A',
                'siteAddress': complaint.customer.site_address if complaint.customer else '',
                'mobileNumber': complaint.contact_person_mobile or complaint.customer.phone if complaint.customer else '',
                'subject': complaint.subject,
                'message': complaint.message,
                'priority': complaint.priority.name if complaint.priority else 'N/A',
                'assigned_to': f"{complaint.assign_to.first_name} {complaint.assign_to.last_name}".strip() or complaint.assign_to.username if complaint.assign_to else 'Unassigned',
                'customer_name': complaint.customer.site_name if complaint.customer else '',
                'contact_person': complaint.contact_person_name or '',
                'block_wing': complaint.block_wing or '',
                'technician_remark': complaint.technician_remark or '',
                'solution': complaint.solution or '',
            })

        return JsonResponse(complaints_data, safe=False)

    except Exception as e:
        logger.error(f"Error getting assigned complaints: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_complaint(request):
    data = request.POST or request.body
    if not isinstance(data, dict):
        import json as _json
        try:
            data = _json.loads(request.body or '{}')
        except Exception:
            data = {}

    try:
        customer = Customer.objects.get(id=data.get('customer')) if data.get('customer') else None
        complaint = Complaint.objects.create(
            complaint_type=ComplaintType.objects.get(id=data['complaint_type']) if data.get('complaint_type') else None,
            date=data.get('date') or None,
            customer=customer,
            contact_person_name=data.get('contact_person_name') or (customer.contact_person_name if customer else ''),
            contact_person_mobile=data.get('contact_person_mobile') or (customer.phone if customer else ''),
            block_wing=data.get('block_wing') or (customer.site_address if customer else ''),
            assign_to=CustomUser.objects.get(id=data['assign_to']) if data.get('assign_to') else None,
            priority=ComplaintPriority.objects.get(id=data['priority']) if data.get('priority') else None,
            status=data.get('status', 'open'),
            subject=data.get('subject', ''),
            message=data.get('message', ''),
            technician_remark=data.get('technician_remark', ''),
            solution=data.get('solution', ''),
        )
        return JsonResponse({'success': True, 'message': f'Complaint {complaint.reference} created successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def update_complaint(request, reference):
    complaint = get_object_or_404(Complaint, reference=reference)
    data = request.POST or request.body
    if not isinstance(data, dict):
        import json as _json
        try:
            data = _json.loads(request.body or '{}')
        except Exception:
            data = {}
    try:
        if data.get('complaint_type'):
            complaint.complaint_type = ComplaintType.objects.get(id=data['complaint_type'])
        if data.get('date'):
            complaint.date = data.get('date')
        if data.get('customer'):
            complaint.customer = Customer.objects.get(id=data['customer'])
        complaint.contact_person_name = data.get('contact_person_name', complaint.contact_person_name)
        complaint.contact_person_mobile = data.get('contact_person_mobile', complaint.contact_person_mobile)
        complaint.block_wing = data.get('block_wing', complaint.block_wing)
        if data.get('assign_to'):
            complaint.assign_to = CustomUser.objects.get(id=data['assign_to'])
        if data.get('priority'):
            complaint.priority = ComplaintPriority.objects.get(id=data['priority'])
        complaint.status = data.get('status', complaint.status)
        complaint.subject = data.get('subject', complaint.subject)
        complaint.message = data.get('message', complaint.message)
        complaint.technician_remark = data.get('technician_remark', complaint.technician_remark)
        complaint.solution = data.get('solution', complaint.solution)
        
        # Handle signature image files
        if 'technician_signature' in request.FILES:
            complaint.technician_signature = request.FILES['technician_signature']
        if 'customer_signature' in request.FILES:
            complaint.customer_signature = request.FILES['customer_signature']
        
        complaint.save()
        return JsonResponse({'success': True, 'message': f'Complaint {complaint.reference} updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def update_complaint_status(request, reference):
    """
    Update complaint status, technician remark, and solution
    Requires token authentication
    """
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Authentication required'}, status=401)

        token_key = auth_header.split(' ')[1]
        from rest_framework.authtoken.models import Token
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # Check if user is in employee group
        if not user.groups.exists():
            return JsonResponse({'error': 'Access denied. Only employees can update complaints'}, status=403)

        # Get complaint
        complaint = get_object_or_404(Complaint, reference=reference)

        # Check if complaint is assigned to this user
        if complaint.assign_to != user:
            return JsonResponse({'error': 'Access denied. Complaint not assigned to you'}, status=403)

        # Parse request data
        data = request.body
        if not isinstance(data, dict):
            import json as _json
            try:
                data = _json.loads(request.body or '{}')
            except Exception:
                data = {}

        # Update fields
        if 'status' in data:
            complaint.status = data['status']
        if 'technician_remark' in data:
            complaint.technician_remark = data['technician_remark']
        if 'solution' in data:
            complaint.solution = data['solution']
        
        # Handle signature image files
        if 'technician_signature' in request.FILES:
            complaint.technician_signature = request.FILES['technician_signature']
        elif 'technician_signature' in data:
            # Handle base64 image data (from mobile apps)
            import base64
            from django.core.files.base import ContentFile
            from django.core.files.uploadedfile import InMemoryUploadedFile
            import io
            
            sig_data = data['technician_signature']
            if sig_data and sig_data.startswith('data:image'):
                # Base64 image data
                try:
                    format, imgstr = sig_data.split(';base64,')
                    ext = format.split('/')[-1]
                    img_data = base64.b64decode(imgstr)
                    img_file = ContentFile(img_data, name=f'tech_sig_{complaint.reference}.{ext}')
                    complaint.technician_signature = img_file
                except Exception as e:
                    logger.error(f"Error processing technician signature: {str(e)}")
            elif sig_data:
                # Try to decode as base64 without data URL prefix
                try:
                    img_data = base64.b64decode(sig_data)
                    img_file = ContentFile(img_data, name=f'tech_sig_{complaint.reference}.png')
                    complaint.technician_signature = img_file
                except Exception:
                    pass
        
        if 'customer_signature' in request.FILES:
            complaint.customer_signature = request.FILES['customer_signature']
        elif 'customer_signature' in data:
            # Handle base64 image data (from mobile apps)
            import base64
            from django.core.files.base import ContentFile
            from django.core.files.uploadedfile import InMemoryUploadedFile
            import io
            
            sig_data = data['customer_signature']
            if sig_data and sig_data.startswith('data:image'):
                # Base64 image data
                try:
                    format, imgstr = sig_data.split(';base64,')
                    ext = format.split('/')[-1]
                    img_data = base64.b64decode(imgstr)
                    img_file = ContentFile(img_data, name=f'cust_sig_{complaint.reference}.{ext}')
                    complaint.customer_signature = img_file
                except Exception as e:
                    logger.error(f"Error processing customer signature: {str(e)}")
            elif sig_data:
                # Try to decode as base64 without data URL prefix
                try:
                    img_data = base64.b64decode(sig_data)
                    img_file = ContentFile(img_data, name=f'cust_sig_{complaint.reference}.png')
                    complaint.customer_signature = img_file
                except Exception:
                    pass

        complaint.save()

        return JsonResponse({
            'success': True,
            'message': f'Complaint {complaint.reference} updated successfully',
            'complaint': {
                'id': complaint.id,
                'reference': complaint.reference,
                'status': complaint.status,
                'technician_remark': complaint.technician_remark,
                'solution': complaint.solution,
            }
        })

    except Exception as e:
        logger.error(f"Error updating complaint status: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# QR Code Generation for Customer
def generate_customer_complaint_qr(request, customer_id):
    """
    Generate a QR code that links to the public complaint form for a specific customer.
    Returns the QR code as base64 image.
    """
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Generate the public complaint URL
        public_url = request.build_absolute_uri(
            reverse('public_complaint_form', args=[customer_id])
        )
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(public_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return JsonResponse({
            'success': True,
            'qr_code': f'data:image/png;base64,{img_str}',
            'url': public_url,
            'customer_name': customer.site_name
        })
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Public Complaint Form (No Authentication Required)
from django.views.decorators.cache import never_cache

@never_cache
def public_complaint_form(request, customer_id):
    """
    Public-facing complaint form that can be accessed via QR code.
    No authentication required.
    """
    try:
        from lift.models import Lift
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get lifts for this customer
        lifts = []
        if customer.job_no:
            lifts = Lift.objects.filter(lift_code=customer.job_no)
        
        # Complaint templates (common issues)
        complaint_templates = [
            "Controller Not in ON Position",
            "Abnormal Noise From Motor",
            "Display Not Working",
            "Cabin Vibration",
            "Door Not Opening/Closing",
            "Lift Not Moving",
            "Emergency Light Not Working",
            "Intercom Not Working",
        ]
        
        context = {
            'customer': customer,
            'lifts': lifts,
            'complaint_templates': complaint_templates,
            'complaint_types': ComplaintType.objects.all().order_by('name'),
            'priorities': ComplaintPriority.objects.all().order_by('name'),
        }
        
        return render(request, 'complaints/public_complaint_form.html', context)
    except Exception as e:
        logger.error(f"Error loading public complaint form: {str(e)}")
        return HttpResponse(f"Error loading form: {str(e)}", status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_public_complaint(request, customer_id):
    """
    Handle public complaint submission (no authentication required).
    """
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get selected complaint templates (checkboxes)
        complaint_templates = request.POST.getlist('complaint_templates[]') or request.POST.getlist('complaint_templates')
        templates_text = ", ".join(complaint_templates) if complaint_templates else ""
        
        # Get lift selection
        lift_info = request.POST.get('lift', '')
        
        # Build the message
        message_parts = []
        if lift_info:
            message_parts.append(f"Lift: {lift_info}")
        if templates_text:
            message_parts.append(f"Issues: {templates_text}")
        if request.POST.get('complaint_details'):
            message_parts.append(f"Details: {request.POST.get('complaint_details')}")
        
        final_message = "\n".join(message_parts)
        
        # Get data from POST
        complaint = Complaint.objects.create(
            complaint_type=ComplaintType.objects.get(id=request.POST.get('complaint_type')) if request.POST.get('complaint_type') else None,
            customer=customer,
            contact_person_name=request.POST.get('contact_person_name', customer.contact_person_name or ''),
            contact_person_mobile=request.POST.get('contact_person_mobile', customer.phone or ''),
            block_wing=request.POST.get('block_wing', customer.site_address or ''),
            lift_info=lift_info,  # Store lift selection
            complaint_templates=templates_text,  # Store selected templates
            priority=ComplaintPriority.objects.get(id=request.POST.get('priority')) if request.POST.get('priority') else None,
            status='open',  # Default status for public complaints
            subject=templates_text or "Lift Complaint",
            message=final_message,
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Complaint {complaint.reference} submitted successfully. Our team will contact you soon.',
            'complaint_reference': complaint.reference
        })
    except Exception as e:
        logger.error(f"Error submitting public complaint: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
