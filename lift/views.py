import json
from datetime import datetime
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
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