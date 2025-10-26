import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import AMC, AMCType, PaymentTerms, Customer
from django.utils import timezone
from datetime import date, timedelta
from items.models import Item

# Create your views here.

def amc_form(request, pk=None):
    """View for AMC form page"""
    # Get customer ID from query parameters if provided
    customer_id = request.GET.get('customerId')
    
    context = {
        'is_edit': pk is not None,
        'amc_id': pk,
        'customer_id': customer_id,
    }
    return render(request, 'amc/add_amc_custom.html', context)

def customer_form(request, pk=None):
    """View for Customer form page"""
    context = {
        'is_edit': pk is not None,
        'customer_id': pk,
    }
    return render(request, 'amc/customer_form.html', context)

# API endpoints for fetching dropdown options
@require_http_methods(["GET"])
def get_amc_types(request):
    """Get all AMC types"""
    try:
        amc_types = AMCType.objects.all().order_by('name')
        data = [
            {"id": amc_type.id, "name": amc_type.name}
            for amc_type in amc_types
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def get_payment_terms(request):
    """Get all payment terms"""
    try:
        payment_terms = PaymentTerms.objects.all().order_by('name')
        data = [
            {"id": term.id, "name": term.name}
            for term in payment_terms
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# CRUD operations for AMC types
@csrf_exempt
@require_http_methods(["POST"])
def create_amc_type(request):
    """Create a new AMC type"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        if AMCType.objects.filter(name=name).exists():
            return JsonResponse({"error": "AMC type already exists"}, status=400)

        amc_type = AMCType.objects.create(name=name)
        return JsonResponse({
            "success": True,
            "id": amc_type.id,
            "name": amc_type.name
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_amc_type(request, amc_type_id):
    """Update an existing AMC type"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        try:
            amc_type = AMCType.objects.get(id=amc_type_id)
        except AMCType.DoesNotExist:
            return JsonResponse({"error": "AMC type not found"}, status=404)

        if AMCType.objects.filter(name=name).exclude(id=amc_type_id).exists():
            return JsonResponse({"error": "AMC type already exists"}, status=400)

        amc_type.name = name
        amc_type.save()

        return JsonResponse({
            "success": True,
            "id": amc_type.id,
            "name": amc_type.name
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_amc_type(request, amc_type_id):
    """Delete an AMC type"""
    try:
        try:
            amc_type = AMCType.objects.get(id=amc_type_id)
        except AMCType.DoesNotExist:
            return JsonResponse({"error": "AMC type not found"}, status=404)

        # Check if AMC type is being used by any AMC
        if AMC.objects.filter(amc_type=amc_type).exists():
            return JsonResponse({
                "error": "Cannot delete AMC type as it is being used by existing AMCs"
            }, status=400)

        name = amc_type.name
        amc_type.delete()

        return JsonResponse({
            "success": True,
            "message": f"AMC type '{name}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# CRUD operations for payment terms
@csrf_exempt
@require_http_methods(["POST"])
def create_payment_term(request):
    """Create a new payment term"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        if PaymentTerms.objects.filter(name=name).exists():
            return JsonResponse({"error": "Payment term already exists"}, status=400)

        payment_term = PaymentTerms.objects.create(name=name)
        return JsonResponse({
            "success": True,
            "id": payment_term.id,
            "name": payment_term.name
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_payment_term(request, payment_term_id):
    """Update an existing payment term"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        try:
            payment_term = PaymentTerms.objects.get(id=payment_term_id)
        except PaymentTerms.DoesNotExist:
            return JsonResponse({"error": "Payment term not found"}, status=404)

        if PaymentTerms.objects.filter(name=name).exclude(id=payment_term_id).exists():
            return JsonResponse({"error": "Payment term already exists"}, status=400)

        payment_term.name = name
        payment_term.save()

        return JsonResponse({
            "success": True,
            "id": payment_term.id,
            "name": payment_term.name
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_payment_term(request, payment_term_id):
    """Delete a payment term"""
    try:
        try:
            payment_term = PaymentTerms.objects.get(id=payment_term_id)
        except PaymentTerms.DoesNotExist:
            return JsonResponse({"error": "Payment term not found"}, status=404)

        # Check if payment term is being used by any AMC
        if AMC.objects.filter(payment_terms=payment_term).exists():
            return JsonResponse({
                "error": "Cannot delete payment term as it is being used by existing AMCs"
            }, status=400)

        name = payment_term.name
        payment_term.delete()

        return JsonResponse({
            "success": True,
            "message": f"Payment term '{name}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

# ... (existing code above) ...


@csrf_exempt
@require_http_methods(["GET", "POST"])
def amc_types_list(request):
    if request.method == 'GET':
        return get_amc_types(request)
    elif request.method == 'POST':
        return create_amc_type(request)

@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def amc_types_detail(request, amc_type_id):
    if request.method == 'PUT':
        return update_amc_type(request, amc_type_id)
    elif request.method == 'DELETE':
        return delete_amc_type(request, amc_type_id)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def payment_terms_list(request):
    if request.method == 'GET':
        return get_payment_terms(request)
    elif request.method == 'POST':
        return create_payment_term(request)

@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def payment_terms_detail(request, payment_term_id):
    if request.method == 'PUT':
        return update_payment_term(request, payment_term_id)
    elif request.method == 'DELETE':
        return delete_payment_term(request, payment_term_id)

# New view for individual customer JSON (to support autofill)
def get_customer_json(request, id):
    try:
        customer = get_object_or_404(Customer, id=id)
        data = {
            'site_address': customer.site_address,
            'job_no': customer.job_no,
            'site_name': customer.site_name,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def get_next_amc_reference(request):
    """Return the next AMC reference ID e.g., AMC01, AMC02"""
    try:
        last_amc = AMC.objects.order_by("id").last()
        last_id = 0
        if last_amc and last_amc.reference_id and last_amc.reference_id.startswith("AMC"):
            try:
                last_id = int(last_amc.reference_id.replace("AMC", ""))
            except ValueError:
                last_id = 0
        next_ref = f"AMC{str(last_id + 1).zfill(2)}"
        return JsonResponse({"reference_id": next_ref})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ================================
# Read-only AMC expiry listings
# ================================

def _month_range(target_date: date):
    first_day = target_date.replace(day=1)
    if first_day.month == 12:
        next_month_first = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month_first = first_day.replace(month=first_day.month + 1, day=1)
    last_day = next_month_first - timedelta(days=1)
    return first_day, last_day


def amc_expiring_this_month(request):
    today = timezone.now().date()
    start, end = _month_range(today)
    amcs = AMC.objects.filter(end_date__gte=start, end_date__lte=end).order_by("end_date")
    context = {"title": "This Month Expiring AMCs", "amcs": amcs}
    return render(request, "amc/amc_expiring_this_month.html", context)


def amc_expiring_last_month(request):
    today = timezone.now().date()
    first_of_this_month = today.replace(day=1)
    last_month_last_day = first_of_this_month - timedelta(days=1)
    start, end = _month_range(last_month_last_day)
    amcs = AMC.objects.filter(end_date__gte=start, end_date__lte=end).order_by("end_date")
    context = {"title": "Last Month Expired AMCs", "amcs": amcs}
    return render(request, "amc/amc_expiring_last_month.html", context)


def amc_expiring_next_month(request):
    today = timezone.now().date()
    # first day of next month
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    start, end = _month_range(next_month_first)
    amcs = AMC.objects.filter(end_date__gte=start, end_date__lte=end).order_by("end_date")
    context = {"title": "Next Month Expiring AMCs", "amcs": amcs}
    return render(request, "amc/amc_expiring_next_month.html", context)


# ================================
# AMC Renewal views
# ================================

def renew_amc_page(request, pk):
    """Render the renewal page with modal"""
    amc = get_object_or_404(AMC, pk=pk)
    context = {
        'amc': amc,
        'amc_types': AMCType.objects.all(),
    }
    return render(request, 'amc/renew_amc.html', context)


@require_http_methods(["GET"])
def get_amc_renewal_data(request, pk):
    """Get AMC data for renewal (pre-fill form)"""
    try:
        amc = get_object_or_404(AMC, pk=pk)
        
        # Calculate new dates (start after current end date, end date +1 year)
        new_start_date = amc.end_date + timedelta(days=1) if amc.end_date else date.today()
        new_end_date = new_start_date + timedelta(days=365)
        
        data = {
            'customer_id': amc.customer.id,
            'customer_name': amc.customer.site_name,
            'amcname': amc.amcname,
            'start_date': new_start_date.strftime('%Y-%m-%d'),
            'end_date': new_end_date.strftime('%Y-%m-%d'),
            'amc_type_id': amc.amc_type.id if amc.amc_type else None,
            'amc_type_name': amc.amc_type.name if amc.amc_type else '',
            'no_of_services': amc.no_of_services,
            'price': float(amc.price),
            'no_of_lifts': amc.no_of_lifts,
            'gst_percentage': float(amc.gst_percentage),
            'equipment_no': amc.equipment_no,
            'latitude': amc.latitude,
            'notes': amc.notes,
            'invoice_frequency': amc.invoice_frequency,
            'amc_service_item_id': amc.amc_service_item.id if amc.amc_service_item else None,
            'is_generate_contract': amc.is_generate_contract,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_renewed_amc(request):
    """Create a new AMC based on renewal data"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['customer', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field.replace("_", " ").title()} is required'
                }, status=400)
        
        # Get customer
        customer = Customer.objects.filter(id=data['customer']).first()
        if not customer:
            return JsonResponse({
                'success': False,
                'error': 'Invalid customer selected'
            }, status=400)
        
        # Get foreign key objects
        amc_type = None
        if data.get('amc_type'):
            amc_type = AMCType.objects.filter(id=data['amc_type']).first()
        
        amc_service_item = None
        if data.get('amc_service_item'):
            amc_service_item = Item.objects.filter(id=data['amc_service_item']).first()
        
        # Validate contract generation
        generate_contract = data.get('is_generate_contract', False)
        if isinstance(generate_contract, str):
            generate_contract = generate_contract.lower() in ('true', 'on', '1')
        if generate_contract and not amc_service_item:
            return JsonResponse({
                'success': False,
                'error': 'Please select an AMC Service Item when generating contract'
            }, status=400)

        # Create renewed AMC
        amc = AMC.objects.create(
            customer=customer,
            amcname=data.get('amcname', ''),
            invoice_frequency=data.get('invoice_frequency', 'annually'),
            amc_type=amc_type,
            start_date=data['start_date'],
            end_date=data['end_date'],
            equipment_no=data.get('equipment_no', ''),
            latitude=data.get('latitude', ''),
            notes=data.get('notes', ''),
            is_generate_contract=generate_contract,
            no_of_services=data.get('no_of_services', 12),
            amc_service_item=amc_service_item,
            price=data.get('price', 0),
            no_of_lifts=data.get('no_of_lifts', 0),
            gst_percentage=data.get('gst_percentage', 0),
            total_amount_paid=data.get('total_amount_paid', 0),
        )

        return JsonResponse({
            'success': True,
            'message': 'AMC renewed successfully',
            'amc': {
                'id': amc.id,
                'reference_id': amc.reference_id,
                'customer': customer.site_name,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)