from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
import json
from .models import TravelRequest

User = get_user_model()

@csrf_exempt
def travel_request_list(request):
    """List all travel requests for the authenticated user"""
    if request.method == 'GET':
        # Get the user from token (assuming token authentication)
        # For now, we'll get all requests - in production you'd filter by user
        travel_requests = TravelRequest.objects.select_related('created_by').all()

        data = []
        for tr in travel_requests:
            data.append({
                'id': tr.id,
                'travel_by': tr.travel_by,
                'travel_date': tr.travel_date.strftime('%Y-%m-%d'),
                'from_place': tr.from_place,
                'to_place': tr.to_place,
                'amount': str(tr.amount),
                'attachment': tr.attachment.url if tr.attachment else None,
                'created_by': tr.created_by.username,
                'created_at': tr.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def travel_request_create(request):
    """Create a new travel request"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Get the authenticated user - for now we'll use a default user
            # In production, you'd get this from the token
            try:
                user = User.objects.first()  # Get first user for demo
                if not user:
                    return JsonResponse({'error': 'No users found'}, status=400)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            travel_request = TravelRequest.objects.create(
                travel_by=data.get('travel_by', 'other'),
                travel_date=data.get('travel_date'),
                from_place=data.get('from_place'),
                to_place=data.get('to_place'),
                amount=data.get('amount'),
                attachment=data.get('attachment'),  # Handle file upload separately
                created_by=user,
            )
            return JsonResponse({
                'id': travel_request.id,
                'message': 'Travel request created successfully'
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def travel_request_detail(request, pk):
    """Get a specific travel request"""
    if request.method == 'GET':
        try:
            travel_request = get_object_or_404(TravelRequest.objects.select_related('created_by'), pk=pk)
            data = {
                'id': travel_request.id,
                'travel_by': travel_request.travel_by,
                'travel_date': travel_request.travel_date.strftime('%Y-%m-%d'),
                'from_place': travel_request.from_place,
                'to_place': travel_request.to_place,
                'amount': str(travel_request.amount),
                'attachment': travel_request.attachment.url if travel_request.attachment else None,
                'created_by': travel_request.created_by.username,
                'created_at': travel_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def travel_request_update(request, pk):
    """Update a travel request"""
    if request.method == 'PUT':
        try:
            travel_request = get_object_or_404(TravelRequest, pk=pk)
            data = json.loads(request.body)

            travel_request.travel_by = data.get('travel_by', travel_request.travel_by)
            travel_request.travel_date = data.get('travel_date', travel_request.travel_date)
            travel_request.from_place = data.get('from_place', travel_request.from_place)
            travel_request.to_place = data.get('to_place', travel_request.to_place)
            travel_request.amount = data.get('amount', travel_request.amount)
            if data.get('attachment'):
                travel_request.attachment = data.get('attachment')

            travel_request.save()

            return JsonResponse({'message': 'Travel request updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def travel_request_delete(request, pk):
    """Delete a travel request"""
    if request.method == 'DELETE':
        try:
            travel_request = get_object_or_404(TravelRequest, pk=pk)
            travel_request.delete()
            return JsonResponse({'message': 'Travel request deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
