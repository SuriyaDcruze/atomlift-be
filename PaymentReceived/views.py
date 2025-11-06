from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import PaymentReceived
from customer.models import Customer
from invoice.models import Invoice


def add_payment_received_custom(request):
    # Get customerId from URL parameter if provided
    customer_id = request.GET.get('customerId', None)
    preselected_customer = None
    if customer_id:
        try:
            preselected_customer = Customer.objects.get(id=customer_id)
        except (Customer.DoesNotExist, ValueError):
            pass
    
    return render(request, 'payments/add_payment_received_custom.html', {
        'is_edit': False,
        'preselected_customer': preselected_customer
    })


def edit_payment_received_custom(request, payment_number):
    payment = get_object_or_404(PaymentReceived, payment_number=payment_number)
    return render(request, 'payments/edit_payment_received_custom.html', {'is_edit': True, 'payment': payment})


@require_http_methods(["GET"])
def get_customers(request):
    data = [{
        'id': c.id,
        'site_name': c.site_name,
    } for c in Customer.objects.all().order_by('site_name')]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_invoices(request):
    data = [{
        'id': i.id,
        'number': getattr(i, 'reference_id', i.id),
        'customer_id': i.customer_id if hasattr(i, 'customer_id') else None,
    } for i in Invoice.objects.all().order_by('-id')]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_next_payment_number(request):
    last = PaymentReceived.objects.order_by('id').last()
    next_id = 1
    if last and last.payment_number and last.payment_number.startswith('PAY'):
        try:
            next_id = int(last.payment_number.replace('PAY', '')) + 1
        except ValueError:
            next_id = 1
    return JsonResponse({'payment_number': f'PAY{next_id:03d}'})


@csrf_exempt
@require_http_methods(["POST"])
def create_payment_received(request):
    import json as _json
    data = request.POST or {}
    if not data:
        try:
            data = _json.loads(request.body or '{}')
        except Exception:
            data = {}
    try:
        # Validate required fields
        if not data.get('customer'):
            return JsonResponse({
                'success': False,
                'error': 'Customer is required. Please select a customer.'
            }, status=400)
        
        amount = data.get('amount')
        if not amount or float(amount) <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Amount is required and must be greater than 0.'
            }, status=400)
        
        payment = PaymentReceived.objects.create(
            customer=Customer.objects.get(id=data['customer']),
            invoice=Invoice.objects.get(id=data['invoice']) if data.get('invoice') else None,
            amount=float(amount),
            date=data.get('date') or None,
            payment_type=data.get('payment_type') or 'cash',
            tax_deducted=data.get('tax_deducted') or 'no',
        )
        return JsonResponse({'success': True, 'message': f'Payment {payment.payment_number} created successfully'})
    except ValidationError as e:
        # Handle validation errors
        if e.message_dict:
            error_fields = ['customer', 'amount']
            for field in error_fields:
                if field in e.message_dict:
                    error_message = e.message_dict[field][0]
                    return JsonResponse({'success': False, 'error': error_message}, status=400)
            error_message = list(e.message_dict.values())[0][0]
        else:
            error_message = str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def update_payment_received(request, payment_number):
    import json as _json
    payment = get_object_or_404(PaymentReceived, payment_number=payment_number)
    data = request.POST or {}
    if not data:
        try:
            data = _json.loads(request.body or '{}')
        except Exception:
            data = {}
    try:
        # Validate required fields
        if not data.get('customer'):
            return JsonResponse({
                'success': False,
                'error': 'Customer is required. Please select a customer.'
            }, status=400)
        
        amount = data.get('amount')
        if not amount or float(amount) <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Amount is required and must be greater than 0.'
            }, status=400)
        
        payment.customer = Customer.objects.get(id=data['customer'])
        if data.get('invoice'):
            payment.invoice = Invoice.objects.get(id=data['invoice'])
        payment.amount = float(amount)
        if data.get('date'):
            payment.date = data.get('date')
        if data.get('payment_type'):
            payment.payment_type = data.get('payment_type')
        if data.get('tax_deducted'):
            payment.tax_deducted = data.get('tax_deducted')
        payment.save()
        return JsonResponse({'success': True, 'message': f'Payment {payment.payment_number} updated successfully'})
    except ValidationError as e:
        # Handle validation errors
        if e.message_dict:
            error_fields = ['customer', 'amount']
            for field in error_fields:
                if field in e.message_dict:
                    error_message = e.message_dict[field][0]
                    return JsonResponse({'success': False, 'error': error_message}, status=400)
            error_message = list(e.message_dict.values())[0][0]
        else:
            error_message = str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

