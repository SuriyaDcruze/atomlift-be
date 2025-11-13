import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Customer, Route, Branch, ProvinceState
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .serializers import CustomerCreateSerializer, CustomerListSerializer

def customer_details(request, pk):
    try:
        c = Customer.objects.get(pk=pk)
        return JsonResponse({
            "site_address": c.site_address,
            "job_no": c.job_no,
        })
    except Customer.DoesNotExist:
        return JsonResponse({}, status=404)

# API endpoints for fetching dropdown options
@require_http_methods(["GET"])
def get_states(request):
    """Get all states/provinces"""
    try:
        states = ProvinceState.objects.all().order_by('value')
        data = [
            {"id": state.id, "value": state.value}
            for state in states
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def get_routes(request):
    """Get all routes"""
    try:
        routes = Route.objects.all().order_by('value')
        data = [
            {"id": route.id, "value": route.value}
            for route in routes
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def get_branches(request):
    """Get all branches"""
    try:
        branches = Branch.objects.all().order_by('value')
        data = [
            {"id": branch.id, "value": branch.value}
            for branch in branches
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def get_next_customer_reference(request):
    """Return the next Customer reference ID e.g., ATOM001"""
    try:
        last = Customer.objects.order_by('id').last()
        if last and last.reference_id and last.reference_id.startswith('ATOM'):
            try:
                next_id = int(last.reference_id.replace('ATOM', '')) + 1
            except ValueError:
                next_id = 1
        else:
            next_id = 1
        next_ref = f'ATOM{next_id:03d}'
        return JsonResponse({"reference_id": next_ref})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Mobile app API: Create Customer
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_customer_mobile(request):
    """Create a new customer from the mobile app (token auth required)."""
    try:
        # Only allow employees (users in at least one group)
        if not request.user.groups.exists():
            return Response({"error": "Access denied. Only employees can add customers."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CustomerCreateSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            data = {
                "id": customer.id,
                "reference_id": customer.reference_id,
                "site_name": customer.site_name,
                "job_no": customer.job_no,
                "email": customer.email,
                "phone": customer.phone,
            }
            return Response({"message": "Customer created successfully", "customer": data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_customers_mobile(request):
    """List customers for mobile app with pagination and filters."""
    try:
        if not request.user.groups.exists():
            return Response({"error": "Access denied. Only employees can view customers."}, status=status.HTTP_403_FORBIDDEN)

        queryset = Customer.objects.all().order_by('-id')

        # Filters
        search = request.query_params.get('q')
        branch_id = request.query_params.get('branch')
        route_id = request.query_params.get('route')
        sector = request.query_params.get('sector')

        if search:
            queryset = queryset.filter(
                Q(site_name__icontains=search) |
                Q(job_no__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(mobile__icontains=search) |
                Q(contact_person_name__icontains=search) |
                Q(city__icontains=search)
            )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if route_id:
            queryset = queryset.filter(routes_id=route_id)
        if sector:
            queryset = queryset.filter(sector=sector)

        paginator = PageNumberPagination()
        page_size = request.query_params.get('page_size')
        if page_size:
            try:
                paginator.page_size = max(1, min(int(page_size), 100))
            except ValueError:
                paginator.page_size = None

        page = paginator.paginate_queryset(queryset, request)
        serializer = CustomerListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CRUD operations for dropdown options
@csrf_exempt
@require_http_methods(["POST"])
def create_state(request):
    """Create a new state/province"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if ProvinceState.objects.filter(value=value).exists():
            return JsonResponse({"error": "State already exists"}, status=400)

        state = ProvinceState.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": state.id,
            "value": state.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_route(request):
    """Create a new route"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if Route.objects.filter(value=value).exists():
            return JsonResponse({"error": "Route already exists"}, status=400)

        route = Route.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": route.id,
            "value": route.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_branch(request):
    """Create a new branch"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if Branch.objects.filter(value=value).exists():
            return JsonResponse({"error": "Branch already exists"}, status=400)

        branch = Branch.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": branch.id,
            "value": branch.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_state(request, state_id):
    """Update an existing state/province"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            state = ProvinceState.objects.get(id=state_id)
        except ProvinceState.DoesNotExist:
            return JsonResponse({"error": "State not found"}, status=404)

        if ProvinceState.objects.filter(value=value).exclude(id=state_id).exists():
            return JsonResponse({"error": "State already exists"}, status=400)

        state.value = value
        state.save()

        return JsonResponse({
            "success": True,
            "id": state.id,
            "value": state.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_route(request, route_id):
    """Update an existing route"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            route = Route.objects.get(id=route_id)
        except Route.DoesNotExist:
            return JsonResponse({"error": "Route not found"}, status=404)

        if Route.objects.filter(value=value).exclude(id=route_id).exists():
            return JsonResponse({"error": "Route already exists"}, status=400)

        route.value = value
        route.save()

        return JsonResponse({
            "success": True,
            "id": route.id,
            "value": route.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_branch(request, branch_id):
    """Update an existing branch"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({"error": "Branch not found"}, status=404)

        if Branch.objects.filter(value=value).exclude(id=branch_id).exists():
            return JsonResponse({"error": "Branch already exists"}, status=400)

        branch.value = value
        branch.save()

        return JsonResponse({
            "success": True,
            "id": branch.id,
            "value": branch.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_state(request, state_id):
    """Delete a state/province"""
    try:
        try:
            state = ProvinceState.objects.get(id=state_id)
        except ProvinceState.DoesNotExist:
            return JsonResponse({"error": "State not found"}, status=404)

        # Check if state is being used by any customer
        if Customer.objects.filter(province_state=state).exists():
            return JsonResponse({
                "error": "Cannot delete state as it is being used by existing customers"
            }, status=400)

        value = state.value
        state.delete()

        return JsonResponse({
            "success": True,
            "message": f"State '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_route(request, route_id):
    """Delete a route"""
    try:
        try:
            route = Route.objects.get(id=route_id)
        except Route.DoesNotExist:
            return JsonResponse({"error": "Route not found"}, status=404)

        # Check if route is being used by any customer
        if Customer.objects.filter(routes=route).exists():
            return JsonResponse({
                "error": "Cannot delete route as it is being used by existing customers"
            }, status=400)

        value = route.value
        route.delete()

        return JsonResponse({
            "success": True,
            "message": f"Route '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_branch(request, branch_id):
    """Delete a branch"""
    try:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({"error": "Branch not found"}, status=404)

        # Check if branch is being used by any customer
        if Customer.objects.filter(branch=branch).exists():
            return JsonResponse({
                "error": "Cannot delete branch as it is being used by existing customers"
            }, status=400)

        value = branch.value
        branch.delete()

        return JsonResponse({
            "success": True,
            "message": f"Branch '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
