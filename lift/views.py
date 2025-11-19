import json
import csv
import io
from datetime import datetime, date
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.contrib import messages
from .models import FloorID, Brand, LiftType, MachineType, MachineBrand, DoorType, DoorBrand, ControllerBrand, Cabin, Lift


# API endpoints for fetching dropdown options
@require_http_methods(["GET"])
def get_floorids(request):
    """Get all floor IDs"""
    try:
        floorids = FloorID.objects.all().order_by('value')
        data = [
            {"id": floorid.id, "value": floorid.value}
            for floorid in floorids
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_brands(request):
    """Get all brands"""
    try:
        brands = Brand.objects.all().order_by('value')
        data = [
            {"id": brand.id, "value": brand.value}
            for brand in brands
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_lifttypes(request):
    """Get all lift types"""
    try:
        lifttypes = LiftType.objects.all().order_by('value')
        data = [
            {"id": lifttype.id, "value": lifttype.value}
            for lifttype in lifttypes
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_machinetypes(request):
    """Get all machine types"""
    try:
        machinetypes = MachineType.objects.all().order_by('value')
        data = [
            {"id": machinetype.id, "value": machinetype.value}
            for machinetype in machinetypes
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_machinebrands(request):
    """Get all machine brands"""
    try:
        machinebrands = MachineBrand.objects.all().order_by('value')
        data = [
            {"id": machinebrand.id, "value": machinebrand.value}
            for machinebrand in machinebrands
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_doortypes(request):
    """Get all door types"""
    try:
        doortypes = DoorType.objects.all().order_by('value')
        data = [
            {"id": doortype.id, "value": doortype.value}
            for doortype in doortypes
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_doorbrands(request):
    """Get all door brands"""
    try:
        doorbrands = DoorBrand.objects.all().order_by('value')
        data = [
            {"id": doorbrand.id, "value": doorbrand.value}
            for doorbrand in doorbrands
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_controllerbrands(request):
    """Get all controller brands"""
    try:
        controllerbrands = ControllerBrand.objects.all().order_by('value')
        data = [
            {"id": controllerbrand.id, "value": controllerbrand.value}
            for controllerbrand in controllerbrands
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_cabins(request):
    """Get all cabins"""
    try:
        cabins = Cabin.objects.all().order_by('value')
        data = [
            {"id": cabin.id, "value": cabin.value}
            for cabin in cabins
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_next_lift_reference(request):
    """Return the next Lift reference ID (predicted) e.g., LIFT-YYYY-0001"""
    try:
        import datetime
        year = datetime.datetime.now().year
        count = Lift.objects.filter(reference_id__startswith=f"LIFT-{year}-").count() + 1
        next_ref = f"LIFT-{year}-{count:04d}"
        return JsonResponse({"reference_id": next_ref})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# CRUD operations for dropdown options
@csrf_exempt
@require_http_methods(["POST"])
def create_floorid(request):
    """Create a new floor ID"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if FloorID.objects.filter(value=value).exists():
            return JsonResponse({"error": "Floor ID already exists"}, status=400)

        floorid = FloorID.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": floorid.id,
            "value": floorid.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_brand(request):
    """Create a new brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if Brand.objects.filter(value=value).exists():
            return JsonResponse({"error": "Brand already exists"}, status=400)

        brand = Brand.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": brand.id,
            "value": brand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_lifttype(request):
    """Create a new lift type"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if LiftType.objects.filter(value=value).exists():
            return JsonResponse({"error": "Lift type already exists"}, status=400)

        lifttype = LiftType.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": lifttype.id,
            "value": lifttype.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_machinetype(request):
    """Create a new machine type"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if MachineType.objects.filter(value=value).exists():
            return JsonResponse({"error": "Machine type already exists"}, status=400)

        machinetype = MachineType.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": machinetype.id,
            "value": machinetype.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_machinebrand(request):
    """Create a new machine brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if MachineBrand.objects.filter(value=value).exists():
            return JsonResponse({"error": "Machine brand already exists"}, status=400)

        machinebrand = MachineBrand.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": machinebrand.id,
            "value": machinebrand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_doortype(request):
    """Create a new door type"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if DoorType.objects.filter(value=value).exists():
            return JsonResponse({"error": "Door type already exists"}, status=400)

        doortype = DoorType.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": doortype.id,
            "value": doortype.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_doorbrand(request):
    """Create a new door brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if DoorBrand.objects.filter(value=value).exists():
            return JsonResponse({"error": "Door brand already exists"}, status=400)

        doorbrand = DoorBrand.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": doorbrand.id,
            "value": doorbrand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_controllerbrand(request):
    """Create a new controller brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if ControllerBrand.objects.filter(value=value).exists():
            return JsonResponse({"error": "Controller brand already exists"}, status=400)

        controllerbrand = ControllerBrand.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": controllerbrand.id,
            "value": controllerbrand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_cabin(request):
    """Create a new cabin"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if Cabin.objects.filter(value=value).exists():
            return JsonResponse({"error": "Cabin already exists"}, status=400)

        cabin = Cabin.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": cabin.id,
            "value": cabin.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_floorid(request, floorid_id):
    """Update an existing floor ID"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            floorid = FloorID.objects.get(id=floorid_id)
        except FloorID.DoesNotExist:
            return JsonResponse({"error": "Floor ID not found"}, status=404)

        if FloorID.objects.filter(value=value).exclude(id=floorid_id).exists():
            return JsonResponse({"error": "Floor ID already exists"}, status=400)

        floorid.value = value
        floorid.save()

        return JsonResponse({
            "success": True,
            "id": floorid.id,
            "value": floorid.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_brand(request, brand_id):
    """Update an existing brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return JsonResponse({"error": "Brand not found"}, status=404)

        if Brand.objects.filter(value=value).exclude(id=brand_id).exists():
            return JsonResponse({"error": "Brand already exists"}, status=400)

        brand.value = value
        brand.save()

        return JsonResponse({
            "success": True,
            "id": brand.id,
            "value": brand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_lifttype(request, lifttype_id):
    """Update an existing lift type"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            lifttype = LiftType.objects.get(id=lifttype_id)
        except LiftType.DoesNotExist:
            return JsonResponse({"error": "Lift type not found"}, status=404)

        if LiftType.objects.filter(value=value).exclude(id=lifttype_id).exists():
            return JsonResponse({"error": "Lift type already exists"}, status=400)

        lifttype.value = value
        lifttype.save()

        return JsonResponse({
            "success": True,
            "id": lifttype.id,
            "value": lifttype.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_machinetype(request, machinetype_id):
    """Update an existing machine type"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            machinetype = MachineType.objects.get(id=machinetype_id)
        except MachineType.DoesNotExist:
            return JsonResponse({"error": "Machine type not found"}, status=404)

        if MachineType.objects.filter(value=value).exclude(id=machinetype_id).exists():
            return JsonResponse({"error": "Machine type already exists"}, status=400)

        machinetype.value = value
        machinetype.save()

        return JsonResponse({
            "success": True,
            "id": machinetype.id,
            "value": machinetype.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_machinebrand(request, machinebrand_id):
    """Update an existing machine brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            machinebrand = MachineBrand.objects.get(id=machinebrand_id)
        except MachineBrand.DoesNotExist:
            return JsonResponse({"error": "Machine brand not found"}, status=404)

        if MachineBrand.objects.filter(value=value).exclude(id=machinebrand_id).exists():
            return JsonResponse({"error": "Machine brand already exists"}, status=400)

        machinebrand.value = value
        machinebrand.save()

        return JsonResponse({
            "success": True,
            "id": machinebrand.id,
            "value": machinebrand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_doortype(request, doortype_id):
    """Update an existing door type"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            doortype = DoorType.objects.get(id=doortype_id)
        except DoorType.DoesNotExist:
            return JsonResponse({"error": "Door type not found"}, status=404)

        if DoorType.objects.filter(value=value).exclude(id=doortype_id).exists():
            return JsonResponse({"error": "Door type already exists"}, status=400)

        doortype.value = value
        doortype.save()

        return JsonResponse({
            "success": True,
            "id": doortype.id,
            "value": doortype.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_doorbrand(request, doorbrand_id):
    """Update an existing door brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            doorbrand = DoorBrand.objects.get(id=doorbrand_id)
        except DoorBrand.DoesNotExist:
            return JsonResponse({"error": "Door brand not found"}, status=404)

        if DoorBrand.objects.filter(value=value).exclude(id=doorbrand_id).exists():
            return JsonResponse({"error": "Door brand already exists"}, status=400)

        doorbrand.value = value
        doorbrand.save()

        return JsonResponse({
            "success": True,
            "id": doorbrand.id,
            "value": doorbrand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_controllerbrand(request, controllerbrand_id):
    """Update an existing controller brand"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            controllerbrand = ControllerBrand.objects.get(id=controllerbrand_id)
        except ControllerBrand.DoesNotExist:
            return JsonResponse({"error": "Controller brand not found"}, status=404)

        if ControllerBrand.objects.filter(value=value).exclude(id=controllerbrand_id).exists():
            return JsonResponse({"error": "Controller brand already exists"}, status=400)

        controllerbrand.value = value
        controllerbrand.save()

        return JsonResponse({
            "success": True,
            "id": controllerbrand.id,
            "value": controllerbrand.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_cabin(request, cabin_id):
    """Update an existing cabin"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            cabin = Cabin.objects.get(id=cabin_id)
        except Cabin.DoesNotExist:
            return JsonResponse({"error": "Cabin not found"}, status=404)

        if Cabin.objects.filter(value=value).exclude(id=cabin_id).exists():
            return JsonResponse({"error": "Cabin already exists"}, status=400)

        cabin.value = value
        cabin.save()

        return JsonResponse({
            "success": True,
            "id": cabin.id,
            "value": cabin.value
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_floorid(request, floorid_id):
    """Delete a floor ID"""
    try:
        try:
            floorid = FloorID.objects.get(id=floorid_id)
        except FloorID.DoesNotExist:
            return JsonResponse({"error": "Floor ID not found"}, status=404)

        if Lift.objects.filter(floor_id=floorid).exists():
            return JsonResponse({
                "error": "Cannot delete Floor ID as it is being used by existing lifts"
            }, status=400)

        value = floorid.value
        floorid.delete()

        return JsonResponse({
            "success": True,
            "message": f"Floor ID '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_brand(request, brand_id):
    """Delete a brand"""
    try:
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return JsonResponse({"error": "Brand not found"}, status=404)

        if Lift.objects.filter(brand=brand).exists():
            return JsonResponse({
                "error": "Cannot delete brand as it is being used by existing lifts"
            }, status=400)

        value = brand.value
        brand.delete()

        return JsonResponse({
            "success": True,
            "message": f"Brand '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_lifttype(request, lifttype_id):
    """Delete a lift type"""
    try:
        try:
            lifttype = LiftType.objects.get(id=lifttype_id)
        except LiftType.DoesNotExist:
            return JsonResponse({"error": "Lift type not found"}, status=404)

        if Lift.objects.filter(lift_type=lifttype).exists():
            return JsonResponse({
                "error": "Cannot delete lift type as it is being used by existing lifts"
            }, status=400)

        value = lifttype.value
        lifttype.delete()

        return JsonResponse({
            "success": True,
            "message": f"Lift type '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_machinetype(request, machinetype_id):
    """Delete a machine type"""
    try:
        try:
            machinetype = MachineType.objects.get(id=machinetype_id)
        except MachineType.DoesNotExist:
            return JsonResponse({"error": "Machine type not found"}, status=404)

        if Lift.objects.filter(machine_type=machinetype).exists():
            return JsonResponse({
                "error": "Cannot delete machine type as it is being used by existing lifts"
            }, status=400)

        value = machinetype.value
        machinetype.delete()

        return JsonResponse({
            "success": True,
            "message": f"Machine type '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_machinebrand(request, machinebrand_id):
    """Delete a machine brand"""
    try:
        try:
            machinebrand = MachineBrand.objects.get(id=machinebrand_id)
        except MachineBrand.DoesNotExist:
            return JsonResponse({"error": "Machine brand not found"}, status=404)

        if Lift.objects.filter(machine_brand=machinebrand).exists():
            return JsonResponse({
                "error": "Cannot delete machine brand as it is being used by existing lifts"
            }, status=400)

        value = machinebrand.value
        machinebrand.delete()

        return JsonResponse({
            "success": True,
            "message": f"Machine brand '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_doortype(request, doortype_id):
    """Delete a door type"""
    try:
        try:
            doortype = DoorType.objects.get(id=doortype_id)
        except DoorType.DoesNotExist:
            return JsonResponse({"error": "Door type not found"}, status=404)

        if Lift.objects.filter(door_type=doortype).exists():
            return JsonResponse({
                "error": "Cannot delete door type as it is being used by existing lifts"
            }, status=400)

        value = doortype.value
        doortype.delete()

        return JsonResponse({
            "success": True,
            "message": f"Door type '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_doorbrand(request, doorbrand_id):
    """Delete a door brand"""
    try:
        try:
            doorbrand = DoorBrand.objects.get(id=doorbrand_id)
        except DoorBrand.DoesNotExist:
            return JsonResponse({"error": "Door brand not found"}, status=404)

        if Lift.objects.filter(door_brand=doorbrand).exists():
            return JsonResponse({
                "error": "Cannot delete door brand as it is being used by existing lifts"
            }, status=400)

        value = doorbrand.value
        doorbrand.delete()

        return JsonResponse({
            "success": True,
            "message": f"Door brand '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_controllerbrand(request, controllerbrand_id):
    """Delete a controller brand"""
    try:
        try:
            controllerbrand = ControllerBrand.objects.get(id=controllerbrand_id)
        except ControllerBrand.DoesNotExist:
            return JsonResponse({"error": "Controller brand not found"}, status=404)

        if Lift.objects.filter(controller_brand=controllerbrand).exists():
            return JsonResponse({
                "error": "Cannot delete controller brand as it is being used by existing lifts"
            }, status=400)

        value = controllerbrand.value
        controllerbrand.delete()

        return JsonResponse({
            "success": True,
            "message": f"Controller brand '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_cabin(request, cabin_id):
    """Delete a cabin"""
    try:
        try:
            cabin = Cabin.objects.get(id=cabin_id)
        except Cabin.DoesNotExist:
            return JsonResponse({"error": "Cabin not found"}, status=404)

        if Lift.objects.filter(cabin=cabin).exists():
            return JsonResponse({
                "error": "Cannot delete cabin as it is being used by existing lifts"
            }, status=400)

        value = cabin.value
        cabin.delete()

        return JsonResponse({
            "success": True,
            "message": f"Cabin '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_floorids(request, pk=None):
    """API for managing floor IDs"""
    if request.method == 'GET':
        floorids = FloorID.objects.all().values('id', 'value')
        return JsonResponse(list(floorids), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if FloorID.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Floor ID already exists'}, status=400)
            floorid = FloorID.objects.create(value=value)
            return JsonResponse({'success': True, 'id': floorid.id, 'value': floorid.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_floorids_detail(request, pk):
    """API for updating/deleting floor IDs"""
    try:
        floorid = get_object_or_404(FloorID, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if FloorID.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Floor ID already exists'}, status=400)
            floorid.value = value
            floorid.save()
            return JsonResponse({'success': True, 'message': 'Floor ID updated'})

        elif request.method == 'DELETE':
            floorid.delete()
            return JsonResponse({'success': True, 'message': 'Floor ID deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_brands(request, pk=None):
    """API for managing brands"""
    if request.method == 'GET':
        brands = Brand.objects.all().values('id', 'value')
        return JsonResponse(list(brands), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if Brand.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Brand already exists'}, status=400)
            brand = Brand.objects.create(value=value)
            return JsonResponse({'success': True, 'id': brand.id, 'value': brand.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_brands_detail(request, pk):
    """API for updating/deleting brands"""
    try:
        brand = get_object_or_404(Brand, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if Brand.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Brand already exists'}, status=400)
            brand.value = value
            brand.save()
            return JsonResponse({'success': True, 'message': 'Brand updated'})

        elif request.method == 'DELETE':
            brand.delete()
            return JsonResponse({'success': True, 'message': 'Brand deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_lifttypes(request, pk=None):
    """API for managing lift types"""
    if request.method == 'GET':
        lifttypes = LiftType.objects.all().values('id', 'value')
        return JsonResponse(list(lifttypes), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if LiftType.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Lift type already exists'}, status=400)
            lifttype = LiftType.objects.create(value=value)
            return JsonResponse({'success': True, 'id': lifttype.id, 'value': lifttype.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_lifttypes_detail(request, pk):
    """API for updating/deleting lift types"""
    try:
        lifttype = get_object_or_404(LiftType, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if LiftType.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Lift type already exists'}, status=400)
            lifttype.value = value
            lifttype.save()
            return JsonResponse({'success': True, 'message': 'Lift type updated'})

        elif request.method == 'DELETE':
            lifttype.delete()
            return JsonResponse({'success': True, 'message': 'Lift type deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_machinetypes(request, pk=None):
    """API for managing machine types"""
    if request.method == 'GET':
        machinetypes = MachineType.objects.all().values('id', 'value')
        return JsonResponse(list(machinetypes), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if MachineType.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Machine type already exists'}, status=400)
            machinetype = MachineType.objects.create(value=value)
            return JsonResponse({'success': True, 'id': machinetype.id, 'value': machinetype.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_machinetypes_detail(request, pk):
    """API for updating/deleting machine types"""
    try:
        machinetype = get_object_or_404(MachineType, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if MachineType.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Machine type already exists'}, status=400)
            machinetype.value = value
            machinetype.save()
            return JsonResponse({'success': True, 'message': 'Machine type updated'})

        elif request.method == 'DELETE':
            machinetype.delete()
            return JsonResponse({'success': True, 'message': 'Machine type deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_machinebrands(request, pk=None):
    """API for managing machine brands"""
    if request.method == 'GET':
        machinebrands = MachineBrand.objects.all().values('id', 'value')
        return JsonResponse(list(machinebrands), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if MachineBrand.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Machine brand already exists'}, status=400)
            machinebrand = MachineBrand.objects.create(value=value)
            return JsonResponse({'success': True, 'id': machinebrand.id, 'value': machinebrand.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_machinebrands_detail(request, pk):
    """API for updating/deleting machine brands"""
    try:
        machinebrand = get_object_or_404(MachineBrand, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if MachineBrand.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Machine brand already exists'}, status=400)
            machinebrand.value = value
            machinebrand.save()
            return JsonResponse({'success': True, 'message': 'Machine brand updated'})

        elif request.method == 'DELETE':
            machinebrand.delete()
            return JsonResponse({'success': True, 'message': 'Machine brand deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_doortypes(request, pk=None):
    """API for managing door types"""
    if request.method == 'GET':
        doortypes = DoorType.objects.all().values('id', 'value')
        return JsonResponse(list(doortypes), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if DoorType.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Door type already exists'}, status=400)
            doortype = DoorType.objects.create(value=value)
            return JsonResponse({'success': True, 'id': doortype.id, 'value': doortype.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_doortypes_detail(request, pk):
    """API for updating/deleting door types"""
    try:
        doortype = get_object_or_404(DoorType, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if DoorType.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Door type already exists'}, status=400)
            doortype.value = value
            doortype.save()
            return JsonResponse({'success': True, 'message': 'Door type updated'})

        elif request.method == 'DELETE':
            doortype.delete()
            return JsonResponse({'success': True, 'message': 'Door type deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_doorbrands(request, pk=None):
    """API for managing door brands"""
    if request.method == 'GET':
        doorbrands = DoorBrand.objects.all().values('id', 'value')
        return JsonResponse(list(doorbrands), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if DoorBrand.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Door brand already exists'}, status=400)
            doorbrand = DoorBrand.objects.create(value=value)
            return JsonResponse({'success': True, 'id': doorbrand.id, 'value': doorbrand.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_doorbrands_detail(request, pk):
    """API for updating/deleting door brands"""
    try:
        doorbrand = get_object_or_404(DoorBrand, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if DoorBrand.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Door brand already exists'}, status=400)
            doorbrand.value = value
            doorbrand.save()
            return JsonResponse({'success': True, 'message': 'Door brand updated'})

        elif request.method == 'DELETE':
            doorbrand.delete()
            return JsonResponse({'success': True, 'message': 'Door brand deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_controllerbrands(request, pk=None):
    """API for managing controller brands"""
    if request.method == 'GET':
        controllerbrands = ControllerBrand.objects.all().values('id', 'value')
        return JsonResponse(list(controllerbrands), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if ControllerBrand.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Controller brand already exists'}, status=400)
            controllerbrand = ControllerBrand.objects.create(value=value)
            return JsonResponse({'success': True, 'id': controllerbrand.id, 'value': controllerbrand.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_controllerbrands_detail(request, pk):
    """API for updating/deleting controller brands"""
    try:
        controllerbrand = get_object_or_404(ControllerBrand, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if ControllerBrand.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Controller brand already exists'}, status=400)
            controllerbrand.value = value
            controllerbrand.save()
            return JsonResponse({'success': True, 'message': 'Controller brand updated'})

        elif request.method == 'DELETE':
            controllerbrand.delete()
            return JsonResponse({'success': True, 'message': 'Controller brand deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_cabins(request, pk=None):
    """API for managing cabins"""
    if request.method == 'GET':
        cabins = Cabin.objects.all().values('id', 'value')
        return JsonResponse(list(cabins), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if Cabin.objects.filter(value=value).exists():
                return JsonResponse({'success': False, 'error': 'Cabin already exists'}, status=400)
            cabin = Cabin.objects.create(value=value)
            return JsonResponse({'success': True, 'id': cabin.id, 'value': cabin.value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_cabins_detail(request, pk):
    """API for updating/deleting cabins"""
    try:
        cabin = get_object_or_404(Cabin, pk=pk)

        if request.method == 'PUT':
            data = json.loads(request.body)
            value = (data.get('value') or '').strip()
            if not value:
                return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
            if Cabin.objects.filter(value=value).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Cabin already exists'}, status=400)
            cabin.value = value
            cabin.save()
            return JsonResponse({'success': True, 'message': 'Cabin updated'})

        elif request.method == 'DELETE':
            cabin.delete()
            return JsonResponse({'success': True, 'message': 'Cabin deleted'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# Custom lift views for add/edit pages
def add_lift_custom(request, job_no=None):
    """Custom add lift page"""
    floor_ids = FloorID.objects.all()
    brands = Brand.objects.all()
    lift_types = LiftType.objects.all()
    machine_types = MachineType.objects.all()
    machine_brands = MachineBrand.objects.all()
    door_types = DoorType.objects.all()
    door_brands = DoorBrand.objects.all()
    controller_brands = ControllerBrand.objects.all()
    cabins = Cabin.objects.all()
    
    # Get customer info if job_no is provided
    customer = None
    suggested_license_no = None
    if job_no:
        try:
            from customer.models import Customer
            customer = Customer.objects.filter(job_no=job_no).first()
            if customer:
                # Get existing lift's license for this customer if any
                from lift.models import Lift
                existing_lift = Lift.objects.filter(lift_code=job_no).first()
                if existing_lift and existing_lift.license_no:
                    suggested_license_no = existing_lift.license_no
        except Exception:
            pass

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get foreign key objects
            floor_id = None
            if data.get('floor_id'):
                floor_id = get_object_or_404(FloorID, id=data['floor_id'])
            
            brand = None
            if data.get('brand'):
                brand = get_object_or_404(Brand, id=data['brand'])
            
            lift_type = None
            if data.get('lift_type'):
                lift_type = get_object_or_404(LiftType, id=data['lift_type'])
            
            machine_type = None
            if data.get('machine_type'):
                machine_type = get_object_or_404(MachineType, id=data['machine_type'])
            
            machine_brand = None
            if data.get('machine_brand'):
                machine_brand = get_object_or_404(MachineBrand, id=data['machine_brand'])
            
            door_type = None
            if data.get('door_type'):
                door_type = get_object_or_404(DoorType, id=data['door_type'])
            
            door_brand = None
            if data.get('door_brand'):
                door_brand = get_object_or_404(DoorBrand, id=data['door_brand'])
            
            controller_brand = None
            if data.get('controller_brand'):
                controller_brand = get_object_or_404(ControllerBrand, id=data['controller_brand'])
            
            cabin = None
            if data.get('cabin'):
                cabin = get_object_or_404(Cabin, id=data['cabin'])
            
            # Validate license dates (optional fields)
            license_start_date = (data.get('license_start_date') or '').strip() or None
            license_end_date = (data.get('license_end_date') or '').strip() or None
            
            # Only validate date order if both dates are provided
            if license_start_date and license_end_date:
                try:
                    start_date = datetime.strptime(license_start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(license_end_date, '%Y-%m-%d').date()
                    if start_date >= end_date:
                        return JsonResponse({
                            'success': False, 
                            'error': 'License start date must be before license end date.'
                        })
                except ValueError:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Invalid date format. Please use YYYY-MM-DD format.'
                    })
            
            # Validate numeric fields
            try:
                price = float(data.get('price', 0))
                if price < 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Price must be a positive number.'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Price must be a valid number.'
                })
            
            try:
                no_of_passengers = int(data.get('no_of_passengers', 0))
                if no_of_passengers < 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Number of passengers must be a positive integer.'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Number of passengers must be a valid integer.'
                })
            
            load_kg = None
            if data.get('load_kg'):
                try:
                    load_kg = int(data.get('load_kg'))
                    if load_kg < 0:
                        return JsonResponse({
                            'success': False,
                            'error': 'Load (kg) must be a positive integer.'
                        })
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'Load (kg) must be a valid integer.'
                    })
            
            # Validate lift_code is provided
            lift_code = data.get('lift_code', '').strip()
            if not lift_code:
                return JsonResponse({'success': False, 'error': 'Lift Code is required. Please enter a lift code.'})
            
            # Validate floor_id is provided
            if not floor_id:
                return JsonResponse({'success': False, 'error': 'Floor ID is required. Please select a floor ID.'})
            
            # Validate brand is provided
            if not brand:
                return JsonResponse({'success': False, 'error': 'Brand is required. Please select a brand.'})
            
            # Validate lift_type is provided
            if not lift_type:
                return JsonResponse({'success': False, 'error': 'Lift Type is required. Please select a lift type.'})
            
            # Validate machine_type is provided
            if not machine_type:
                return JsonResponse({'success': False, 'error': 'Machine Type is required. Please select a machine type.'})
            
            # Validate door_type is provided
            if not door_type:
                return JsonResponse({'success': False, 'error': 'Door Type is required. Please select a door type.'})
            
            # Create new lift
            lift = Lift(
                lift_code=lift_code,
                name=data.get('name', ''),
                price=price,
                floor_id=floor_id,
                brand=brand,
                model=data.get('model', ''),
                no_of_passengers=no_of_passengers,
                load_kg=load_kg,
                speed=data.get('speed', ''),
                lift_type=lift_type,
                machine_type=machine_type,
                machine_brand=machine_brand,
                door_type=door_type,
                door_brand=door_brand,
                controller_brand=controller_brand,
                cabin=cabin,
                block=data.get('block', ''),
                license_no=data.get('license_no', ''),
                license_start_date=license_start_date,
                license_end_date=license_end_date,
            )
            lift.full_clean()
            lift.save()
            return JsonResponse({'success': True, 'message': 'Lift created successfully'})
        except ValidationError as e:
            # Handle validation errors for multiple fields
            if e.message_dict:
                # Prioritize showing field-specific errors
                error_fields = ['lift_code', 'floor_id', 'name', 'model', 'speed', 'brand', 'lift_type', 'machine_type', 'door_type']
                for field in error_fields:
                    if field in e.message_dict:
                        error_message = e.message_dict[field][0]
                        return JsonResponse({'success': False, 'error': error_message})
                # Fallback to first error if none of the prioritized fields have errors
                error_message = list(e.message_dict.values())[0][0]
            else:
                error_message = str(e)
            return JsonResponse({'success': False, 'error': error_message})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'lift/add_lift_custom.html', {
        'floor_ids': floor_ids,
        'brands': brands,
        'lift_types': lift_types,
        'machine_types': machine_types,
        'machine_brands': machine_brands,
        'door_types': door_types,
        'door_brands': door_brands,
        'controller_brands': controller_brands,
        'cabins': cabins,
        'is_edit': False,
        'job_no': job_no,  # Pass job_no to template for pre-filling
        'customer': customer,  # Pass customer for license auto-fill
        'suggested_license_no': suggested_license_no  # Pass suggested license no
    })


def edit_lift_custom(request, identifier):
    """Custom edit lift page"""
    try:
        # Try to find by lift_code first, then by reference_id
        try:
            lift = Lift.objects.get(lift_code=identifier)
        except Lift.DoesNotExist:
            lift = Lift.objects.get(reference_id=identifier)
    except Lift.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Lift not found')
        return render(request, '404.html')

    floor_ids = FloorID.objects.all()
    brands = Brand.objects.all()
    lift_types = LiftType.objects.all()
    machine_types = MachineType.objects.all()
    machine_brands = MachineBrand.objects.all()
    door_types = DoorType.objects.all()
    door_brands = DoorBrand.objects.all()
    controller_brands = ControllerBrand.objects.all()
    cabins = Cabin.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get foreign key objects
            floor_id = None
            if data.get('floor_id'):
                floor_id = get_object_or_404(FloorID, id=data['floor_id'])
            
            brand = None
            if data.get('brand'):
                brand = get_object_or_404(Brand, id=data['brand'])
            
            lift_type = None
            if data.get('lift_type'):
                lift_type = get_object_or_404(LiftType, id=data['lift_type'])
            
            machine_type = None
            if data.get('machine_type'):
                machine_type = get_object_or_404(MachineType, id=data['machine_type'])
            
            machine_brand = None
            if data.get('machine_brand'):
                machine_brand = get_object_or_404(MachineBrand, id=data['machine_brand'])
            
            door_type = None
            if data.get('door_type'):
                door_type = get_object_or_404(DoorType, id=data['door_type'])
            
            door_brand = None
            if data.get('door_brand'):
                door_brand = get_object_or_404(DoorBrand, id=data['door_brand'])
            
            controller_brand = None
            if data.get('controller_brand'):
                controller_brand = get_object_or_404(ControllerBrand, id=data['controller_brand'])
            
            cabin = None
            if data.get('cabin'):
                cabin = get_object_or_404(Cabin, id=data['cabin'])
            
            # Validate license dates (optional fields)
            license_start_date = (data.get('license_start_date') or '').strip() or None
            license_end_date = (data.get('license_end_date') or '').strip() or None
            
            # Only validate date order if both dates are provided
            if license_start_date and license_end_date:
                try:
                    start_date = datetime.strptime(license_start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(license_end_date, '%Y-%m-%d').date()
                    if start_date >= end_date:
                        return JsonResponse({
                            'success': False, 
                            'error': 'License start date must be before license end date.'
                        })
                except ValueError:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Invalid date format. Please use YYYY-MM-DD format.'
                    })
            
            # Validate numeric fields
            try:
                price = float(data.get('price', 0))
                if price < 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Price must be a positive number.'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Price must be a valid number.'
                })
            
            try:
                no_of_passengers = int(data.get('no_of_passengers', 0))
                if no_of_passengers < 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Number of passengers must be a positive integer.'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Number of passengers must be a valid integer.'
                })
            
            load_kg = None
            if data.get('load_kg'):
                try:
                    load_kg = int(data.get('load_kg'))
                    if load_kg < 0:
                        return JsonResponse({
                            'success': False,
                            'error': 'Load (kg) must be a positive integer.'
                        })
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'Load (kg) must be a valid integer.'
                    })
            
            # Validate lift_code is provided
            lift_code = data.get('lift_code', '').strip()
            if not lift_code:
                return JsonResponse({'success': False, 'error': 'Lift Code is required. Please enter a lift code.'})
            
            # Validate floor_id is provided
            if not floor_id:
                return JsonResponse({'success': False, 'error': 'Floor ID is required. Please select a floor ID.'})
            
            # Validate brand is provided
            if not brand:
                return JsonResponse({'success': False, 'error': 'Brand is required. Please select a brand.'})
            
            # Validate lift_type is provided
            if not lift_type:
                return JsonResponse({'success': False, 'error': 'Lift Type is required. Please select a lift type.'})
            
            # Validate machine_type is provided
            if not machine_type:
                return JsonResponse({'success': False, 'error': 'Machine Type is required. Please select a machine type.'})
            
            # Validate door_type is provided
            if not door_type:
                return JsonResponse({'success': False, 'error': 'Door Type is required. Please select a door type.'})
            
            # Update lift
            lift.lift_code = lift_code
            lift.name = data.get('name', '')
            lift.price = price
            lift.floor_id = floor_id
            lift.brand = brand
            lift.model = data.get('model', '')
            lift.no_of_passengers = no_of_passengers
            lift.load_kg = load_kg
            lift.speed = data.get('speed', '')
            lift.lift_type = lift_type
            lift.machine_type = machine_type
            lift.machine_brand = machine_brand
            lift.door_type = door_type
            lift.door_brand = door_brand
            lift.controller_brand = controller_brand
            lift.cabin = cabin
            lift.block = data.get('block', '')
            lift.license_no = data.get('license_no', '')
            lift.license_start_date = license_start_date
            lift.license_end_date = license_end_date
            lift.full_clean()
            lift.save()

            return JsonResponse({'success': True, 'message': 'Lift updated successfully'})
        except ValidationError as e:
            # Handle validation errors for multiple fields
            if e.message_dict:
                # Prioritize showing field-specific errors
                error_fields = ['lift_code', 'floor_id', 'name', 'model', 'speed', 'brand', 'lift_type', 'machine_type', 'door_type']
                for field in error_fields:
                    if field in e.message_dict:
                        error_message = e.message_dict[field][0]
                        return JsonResponse({'success': False, 'error': error_message})
                # Fallback to first error if none of the prioritized fields have errors
                error_message = list(e.message_dict.values())[0][0]
            else:
                error_message = str(e)
            return JsonResponse({'success': False, 'error': error_message})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'lift/add_lift_custom.html', {
        'lift': lift,
        'floor_ids': floor_ids,
        'brands': brands,
        'lift_types': lift_types,
        'machine_types': machine_types,
        'machine_brands': machine_brands,
        'door_types': door_types,
        'door_brands': door_brands,
        'controller_brands': controller_brands,
        'cabins': cabins,
        'is_edit': True
    })


def bulk_import_view(request):
    """View for bulk importing lifts from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'lift/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'lift/bulk_import.html')
            
            # Read file content
            file_content = file.read()
            
            # Parse CSV
            if file_name.endswith('.csv'):
                try:
                    # Try to decode as UTF-8
                    try:
                        decoded_file = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try with different encoding
                        decoded_file = file_content.decode('latin-1')
                    
                    csv_reader = csv.DictReader(io.StringIO(decoded_file))
                    # Normalize headers to lowercase, strip whitespace, and replace spaces with underscores
                    rows = []
                    for row in csv_reader:
                        normalized_row = {}
                        for key, value in row.items():
                            # Normalize key: lowercase, strip, and replace spaces/hyphens with underscores
                            if key:
                                normalized_key = key.strip().lower().replace(' ', '_').replace('-', '_')
                            else:
                                normalized_key = ''
                            # Handle None values and convert to string
                            if value is None:
                                normalized_row[normalized_key] = ''
                            else:
                                normalized_row[normalized_key] = str(value) if value else ''
                        rows.append(normalized_row)
                except Exception as e:
                    messages.error(request, f'Error reading CSV file: {str(e)}')
                    return render(request, 'lift/bulk_import.html')
            else:
                # Parse Excel file
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(io.BytesIO(file_content))
                    sheet = workbook.active
                    
                    # Get headers from first row, convert to lowercase, strip, and replace spaces with underscores
                    headers = []
                    for cell in sheet[1]:
                        header_value = cell.value
                        if header_value:
                            normalized_header = str(header_value).strip().lower().replace(' ', '_').replace('-', '_')
                            headers.append(normalized_header)
                        else:
                            headers.append('')
                    
                    rows = []
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        # Check if row has any non-empty values
                        if any(cell is not None and str(cell).strip() for cell in row if cell is not None):
                            # Create dict with lowercase keys and handle None values
                            row_dict = {}
                            for i, cell_value in enumerate(row):
                                if i < len(headers) and headers[i]:
                                    # Convert None to empty string, then to string
                                    if cell_value is None:
                                        row_dict[headers[i]] = ''
                                    else:
                                        # Handle datetime/date objects from Excel (convert to YYYY-MM-DD format)
                                        if isinstance(cell_value, (datetime, date)):
                                            row_dict[headers[i]] = cell_value.strftime('%Y-%m-%d')
                                        else:
                                            row_dict[headers[i]] = str(cell_value)
                            if row_dict:  # Only add if dict is not empty
                                rows.append(row_dict)
                except ImportError:
                    messages.error(request, 'openpyxl library is required for Excel files. Please install it: pip install openpyxl')
                    return render(request, 'lift/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'lift/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'lift/bulk_import.html')
            
            # Process rows and create lifts
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in enumerate(rows, start=2):  # Start from 2 (1 is header)
                try:
                    # Map CSV columns to model fields - handle None values and empty strings
                    # Headers are normalized to lowercase with underscores, so 'lift_code' should work
                    lift_code_raw = row.get('lift_code', '') or ''
                    lift_code = str(lift_code_raw).strip() if lift_code_raw else ''
                    
                    name_raw = row.get('name', '') or ''
                    name = str(name_raw).strip() if name_raw else ''
                    
                    floor_id_value = row.get('floor_id', '') or ''
                    floor_id_value = str(floor_id_value).strip() if floor_id_value else ''
                    
                    brand_value = row.get('brand', '') or ''
                    brand_value = str(brand_value).strip() if brand_value else ''
                    
                    lift_type_value = row.get('lift_type', '') or ''
                    lift_type_value = str(lift_type_value).strip() if lift_type_value else ''
                    
                    machine_type_value = row.get('machine_type', '') or ''
                    machine_type_value = str(machine_type_value).strip() if machine_type_value else ''
                    
                    door_type_value = row.get('door_type', '') or ''
                    door_type_value = str(door_type_value).strip() if door_type_value else ''
                    
                    model_raw = row.get('model', '') or ''
                    model = str(model_raw).strip() if model_raw else ''
                    
                    speed_raw = row.get('speed', '') or ''
                    speed = str(speed_raw).strip() if speed_raw else ''
                    
                    no_of_passengers_raw = row.get('no_of_passengers', '0') or '0'
                    no_of_passengers = str(no_of_passengers_raw).strip() if no_of_passengers_raw else '0'
                    
                    load_kg_raw = row.get('load_kg', '') or ''
                    load_kg = str(load_kg_raw).strip() if load_kg_raw else ''
                    
                    price_raw = row.get('price', '0') or '0'
                    price = str(price_raw).strip() if price_raw else '0'
                    
                    machine_brand_value = row.get('machine_brand', '') or ''
                    machine_brand_value = str(machine_brand_value).strip() if machine_brand_value else ''
                    
                    door_brand_value = row.get('door_brand', '') or ''
                    door_brand_value = str(door_brand_value).strip() if door_brand_value else ''
                    
                    controller_brand_value = row.get('controller_brand', '') or ''
                    controller_brand_value = str(controller_brand_value).strip() if controller_brand_value else ''
                    
                    cabin_value = row.get('cabin', '') or ''
                    cabin_value = str(cabin_value).strip() if cabin_value else ''
                    
                    block_raw = row.get('block', '') or ''
                    block = str(block_raw).strip() if block_raw else ''
                    
                    license_no_raw = row.get('license_no', '') or ''
                    license_no = str(license_no_raw).strip() if license_no_raw else ''
                    
                    # Handle both 'license_start_date' and 'license_start_date_str' column names
                    license_start_date_raw = row.get('license_start_date', '') or row.get('license_start_date_str', '') or ''
                    license_start_date = str(license_start_date_raw).strip() if license_start_date_raw else ''
                    
                    # Handle both 'license_end_date' and 'license_end_date_str' column names
                    license_end_date_raw = row.get('license_end_date', '') or row.get('license_end_date_str', '') or ''
                    license_end_date = str(license_end_date_raw).strip() if license_end_date_raw else ''
                    
                    # Validate required fields in the same order as add_lift_custom
                    # First validate lift_code (same as add_lift_custom line 1438-1441)
                    lift_code_stripped = lift_code.strip() if lift_code else ''
                    if not lift_code_stripped:
                        errors.append(f'Row {idx}: Lift Code is required. Please enter a lift code.')
                        error_count += 1
                        continue
                    
                    # Check if lift_code already exists (unique constraint)
                    if Lift.objects.filter(lift_code=lift_code_stripped).exists():
                        errors.append(f'Row {idx}: Lift Code "{lift_code_stripped}" already exists. Please use a different lift code.')
                        error_count += 1
                        continue
                    
                    # Validate floor_id (same as add_lift_custom line 1443-1445)
                    if not floor_id_value or len(floor_id_value.strip()) == 0:
                        errors.append(f'Row {idx}: Floor ID is required. Please select a floor ID.')
                        error_count += 1
                        continue
                    
                    # Validate brand (same as add_lift_custom line 1447-1449)
                    if not brand_value or len(brand_value.strip()) == 0:
                        errors.append(f'Row {idx}: Brand is required. Please select a brand.')
                        error_count += 1
                        continue
                    
                    # Validate lift_type (same as add_lift_custom line 1451-1453)
                    if not lift_type_value or len(lift_type_value.strip()) == 0:
                        errors.append(f'Row {idx}: Lift Type is required. Please select a lift type.')
                        error_count += 1
                        continue
                    
                    # Validate machine_type (same as add_lift_custom line 1455-1457)
                    if not machine_type_value or len(machine_type_value.strip()) == 0:
                        errors.append(f'Row {idx}: Machine Type is required. Please select a machine type.')
                        error_count += 1
                        continue
                    
                    # Validate door_type (same as add_lift_custom line 1459-1461)
                    if not door_type_value or len(door_type_value.strip()) == 0:
                        errors.append(f'Row {idx}: Door Type is required. Please select a door type.')
                        error_count += 1
                        continue
                    
                    # Note: speed, name, model are optional in add_lift_custom (not validated as required)
                    # They are validated by full_clean() if provided
                    
                    # Get or create foreign key objects by value (for CSV/Excel, we use values not IDs)
                    floor_id_obj, created = FloorID.objects.get_or_create(value=floor_id_value.strip())
                    brand_obj, created = Brand.objects.get_or_create(value=brand_value.strip())
                    lift_type_obj, created = LiftType.objects.get_or_create(value=lift_type_value.strip())
                    machine_type_obj, created = MachineType.objects.get_or_create(value=machine_type_value.strip())
                    door_type_obj, created = DoorType.objects.get_or_create(value=door_type_value.strip())
                    
                    # Optional foreign keys
                    machine_brand_obj = None
                    if machine_brand_value:
                        machine_brand_obj, created = MachineBrand.objects.get_or_create(value=machine_brand_value)
                    
                    door_brand_obj = None
                    if door_brand_value:
                        door_brand_obj, created = DoorBrand.objects.get_or_create(value=door_brand_value)
                    
                    controller_brand_obj = None
                    if controller_brand_value:
                        controller_brand_obj, created = ControllerBrand.objects.get_or_create(value=controller_brand_value)
                    
                    cabin_obj = None
                    if cabin_value:
                        cabin_obj, created = Cabin.objects.get_or_create(value=cabin_value)
                    
                    # Validate numeric fields (same as add_lift_custom lines 1396-1436)
                    try:
                        price_val = float(price) if price else 0.00
                        if price_val < 0:
                            errors.append(f'Row {idx}: Price must be a positive number.')
                            error_count += 1
                            continue
                    except (ValueError, TypeError):
                        errors.append(f'Row {idx}: Price must be a valid number.')
                        error_count += 1
                        continue
                    
                    try:
                        no_of_passengers_val = int(no_of_passengers) if no_of_passengers else 0
                        if no_of_passengers_val < 0:
                            errors.append(f'Row {idx}: Number of passengers must be a positive integer.')
                            error_count += 1
                            continue
                    except (ValueError, TypeError):
                        errors.append(f'Row {idx}: Number of passengers must be a valid integer.')
                        error_count += 1
                        continue
                    
                    load_kg_val = None
                    if load_kg and load_kg.strip():
                        try:
                            load_kg_val = int(load_kg)
                            if load_kg_val < 0:
                                errors.append(f'Row {idx}: Load (kg) must be a positive integer.')
                                error_count += 1
                                continue
                        except (ValueError, TypeError):
                            errors.append(f'Row {idx}: Load (kg) must be a valid integer.')
                            error_count += 1
                            continue
                    
                    # Validate license dates (same as add_lift_custom lines 1376-1394)
                    # Helper function to parse dates in various formats
                    def parse_date(date_str):
                        """Parse date string in YYYY-MM-DD format or common Excel formats"""
                        if not date_str or not date_str.strip():
                            return None
                        date_str = date_str.strip()
                        
                        # Try YYYY-MM-DD format first (expected format)
                        try:
                            return datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            pass
                        
                        # Try other common formats
                        date_formats = [
                            '%Y/%m/%d',
                            '%d/%m/%Y',
                            '%m/%d/%Y',
                            '%d-%m-%Y',
                            '%m-%d-%Y',
                        ]
                        for fmt in date_formats:
                            try:
                                return datetime.strptime(date_str, fmt).date()
                            except ValueError:
                                continue
                        
                        # If all parsing fails, return None (will be caught by error handling)
                        return None
                    
                    license_start_date_parsed = None
                    license_end_date_parsed = None
                    license_start_date_stripped = license_start_date.strip() if license_start_date else ''
                    license_end_date_stripped = license_end_date.strip() if license_end_date else ''
                    
                    if license_start_date_stripped:
                        license_start_date_parsed = parse_date(license_start_date_stripped)
                        if license_start_date_parsed is None:
                            errors.append(f'Row {idx}: Invalid license start date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    
                    if license_end_date_stripped:
                        license_end_date_parsed = parse_date(license_end_date_stripped)
                        if license_end_date_parsed is None:
                            errors.append(f'Row {idx}: Invalid license end date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    
                    # Only validate date order if both dates are provided (same as add_lift_custom)
                    if license_start_date_parsed and license_end_date_parsed:
                        if license_start_date_parsed >= license_end_date_parsed:
                            errors.append(f'Row {idx}: License start date must be before license end date.')
                            error_count += 1
                            continue
                    
                    # Create lift (same structure as add_lift_custom lines 1463-1485)
                    lift = Lift(
                        lift_code=lift_code_stripped,
                        name=name.strip() if name else '',
                        price=price_val,
                        floor_id=floor_id_obj,
                        brand=brand_obj,
                        model=model.strip() if model else '',
                        no_of_passengers=no_of_passengers_val,
                        load_kg=load_kg_val,
                        speed=speed.strip() if speed else '',
                        lift_type=lift_type_obj,
                        machine_type=machine_type_obj,
                        machine_brand=machine_brand_obj,
                        door_type=door_type_obj,
                        door_brand=door_brand_obj,
                        controller_brand=controller_brand_obj,
                        cabin=cabin_obj,
                        block=block.strip() if block else '',
                        license_no=license_no.strip() if license_no else '',
                        license_start_date=license_start_date_parsed,
                        license_end_date=license_end_date_parsed,
                    )
                    
                    # Validate and save (same as add_lift_custom - uses full_clean which applies all model validations)
                    try:
                        lift.full_clean()  # This will validate: lift_code, floor_id, brand, lift_type, machine_type, door_type, name, model, speed as per model clean()
                        lift.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors same way as add_lift_custom
                        if e.message_dict:
                            # Prioritize showing field-specific errors (same priority as add_lift_custom)
                            error_fields = ['lift_code', 'floor_id', 'name', 'model', 'speed', 'brand', 'lift_type', 'machine_type', 'door_type']
                            error_msg = None
                            for field in error_fields:
                                if field in e.message_dict:
                                    error_msg = f"Row {idx}: {e.message_dict[field][0]}"
                                    break
                            if not error_msg:
                                # Fallback to first error if none of the prioritized fields have errors
                                error_msg = f"Row {idx}: {list(e.message_dict.values())[0][0]}"
                        else:
                            error_msg = f"Row {idx}: {str(e)}"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    except Exception as e:
                        # Handle unique constraint violations and other database errors
                        error_str = str(e).lower()
                        if 'unique' in error_str or 'duplicate' in error_str or 'already exists' in error_str:
                            if 'lift_code' in error_str or 'reference_id' in error_str:
                                errors.append(f'Row {idx}: Lift Code "{lift_code}" already exists. Please use a different lift code.')
                            else:
                                errors.append(f'Row {idx}: Duplicate entry - {str(e)}')
                        else:
                            errors.append(f'Row {idx}: {str(e)}')
                        error_count += 1
                        continue
                    
                except Exception as e:
                    errors.append(f'Row {idx}: {str(e)}')
                    error_count += 1
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} lift(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if len(errors) <= 10:
                    error_message += ' Errors: ' + '; '.join(errors)
                else:
                    error_message += f' First 10 errors: ' + '; '.join(errors[:10])
                messages.warning(request, error_message)
            
            return render(request, 'lift/bulk_import.html', {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors[:20]  # Show max 20 errors
            })
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'lift/bulk_import.html')
    
    return render(request, 'lift/bulk_import.html')