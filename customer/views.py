import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Customer, Route, Branch, ProvinceState

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
