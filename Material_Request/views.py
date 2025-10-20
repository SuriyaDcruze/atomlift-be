from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import MaterialRequest

def frontend_view(request):
    """Serve the React frontend for Material Request"""
    return render(request, 'Material_Request/frontend.html')

@csrf_exempt
def material_request_list(request):
    """List all material requests or create a new one"""
    if request.method == 'GET':
        material_requests = MaterialRequest.objects.all()
        data = []
        for mr in material_requests:
            data.append({
                'id': mr.id,
                'date': mr.date.strftime('%Y-%m-%d'),
                'name': mr.name,
                'description': mr.description,
                'item': mr.item,
                'brand': mr.brand,
                'file': mr.file,
                'added_by': mr.added_by,
                'requested_by': mr.requested_by,
            })
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_create(request):
    """Create a new material request"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_request = MaterialRequest.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                item=data.get('item'),
                brand=data.get('brand', ''),
                file=data.get('file', ''),
                added_by=data.get('added_by'),
                requested_by=data.get('requested_by'),
            )
            return JsonResponse({
                'id': material_request.id,
                'message': 'Material request created successfully'
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_detail(request, pk):
    """Get a specific material request"""
    if request.method == 'GET':
        try:
            material_request = get_object_or_404(MaterialRequest, pk=pk)
            data = {
                'id': material_request.id,
                'date': material_request.date.strftime('%Y-%m-%d'),
                'name': material_request.name,
                'description': material_request.description,
                'item': material_request.item,
                'brand': material_request.brand,
                'file': material_request.file,
                'added_by': material_request.added_by,
                'requested_by': material_request.requested_by,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_update(request, pk):
    """Update a material request"""
    if request.method == 'PUT':
        try:
            material_request = get_object_or_404(MaterialRequest, pk=pk)
            data = json.loads(request.body)

            material_request.name = data.get('name', material_request.name)
            material_request.description = data.get('description', material_request.description)
            material_request.item = data.get('item', material_request.item)
            material_request.brand = data.get('brand', material_request.brand)
            material_request.file = data.get('file', material_request.file)
            material_request.added_by = data.get('added_by', material_request.added_by)
            material_request.requested_by = data.get('requested_by', material_request.requested_by)

            material_request.save()

            return JsonResponse({'message': 'Material request updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def material_request_delete(request, pk):
    """Delete a material request"""
    if request.method == 'DELETE':
        try:
            material_request = get_object_or_404(MaterialRequest, pk=pk)
            material_request.delete()
            return JsonResponse({'message': 'Material request deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
