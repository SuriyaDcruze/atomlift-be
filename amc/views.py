import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import AMC, AMCType, PaymentTerms

# Create your views here.

def amc_form(request, pk=None):
    """View for AMC form page"""
    context = {
        'is_edit': pk is not None,
        'amc_id': pk,
    }
    return render(request, 'amc/amc_form.html', context)

def customer_form(request, pk=None):
    """View for Customer form page"""
    context = {
        'is_edit': pk is not None,
        'customer_id': pk,
    }

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
