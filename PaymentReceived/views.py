from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import PaymentReceived
from customer.models import Customer
from invoice.models import Invoice


def add_payment_received_custom(request):
    return render(request, 'payments/add_payment_received_custom.html', {'is_edit': False})


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
        payment = PaymentReceived.objects.create(
            customer=Customer.objects.get(id=data['customer']) if data.get('customer') else None,
            invoice=Invoice.objects.get(id=data['invoice']) if data.get('invoice') else None,
            amount=data.get('amount') or 0,
            date=data.get('date') or None,
            payment_type=data.get('payment_type') or 'cash',
            tax_deducted=data.get('tax_deducted') or 'no',
        )
        return JsonResponse({'success': True, 'message': f'Payment {payment.payment_number} created successfully'})
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
        if data.get('customer'):
            payment.customer = Customer.objects.get(id=data['customer'])
        if data.get('invoice'):
            payment.invoice = Invoice.objects.get(id=data['invoice'])
        if data.get('amount') is not None:
            payment.amount = data.get('amount')
        if data.get('date'):
            payment.date = data.get('date')
        if data.get('payment_type'):
            payment.payment_type = data.get('payment_type')
        if data.get('tax_deducted'):
            payment.tax_deducted = data.get('tax_deducted')
        payment.save()
        return JsonResponse({'success': True, 'message': f'Payment {payment.payment_number} updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

