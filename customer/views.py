import csv
import io
from datetime import datetime, date
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Customer, Route, Branch, ProvinceState, City
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
def get_cities(request):
    """Get all cities"""
    try:
        cities = City.objects.all().order_by('value')
        data = [
            {"id": city.id, "value": city.value}
            for city in cities
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
            Q(city__value__icontains=search)
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
@require_http_methods(["POST"])
def create_city(request):
    """Create a new city"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        if City.objects.filter(value=value).exists():
            return JsonResponse({"error": "City already exists"}, status=400)

        city = City.objects.create(value=value)
        return JsonResponse({
            "success": True,
            "id": city.id,
            "value": city.value
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
@require_http_methods(["PUT"])
def update_city(request, city_id):
    """Update an existing city"""
    try:
        data = json.loads(request.body)
        value = data.get('value', '').strip()

        if not value:
            return JsonResponse({"error": "Value is required"}, status=400)

        try:
            city = City.objects.get(id=city_id)
        except City.DoesNotExist:
            return JsonResponse({"error": "City not found"}, status=404)

        if City.objects.filter(value=value).exclude(id=city_id).exists():
            return JsonResponse({"error": "City already exists"}, status=400)

        city.value = value
        city.save()

        return JsonResponse({
            "success": True,
            "id": city.id,
            "value": city.value
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

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_city(request, city_id):
    """Delete a city"""
    try:
        try:
            city = City.objects.get(id=city_id)
        except City.DoesNotExist:
            return JsonResponse({"error": "City not found"}, status=404)

        # Check if city is being used by any customer
        if Customer.objects.filter(city=city).exists():
            return JsonResponse({
                "error": "Cannot delete city as it is being used by existing customers"
            }, status=400)

        value = city.value
        city.delete()

        return JsonResponse({
            "success": True,
            "message": f"City '{value}' deleted successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def bulk_import_view(request):
    """View for bulk importing customers from CSV/Excel"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'customer/bulk_import.html')
            
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
                return render(request, 'customer/bulk_import.html')
            
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
                    return render(request, 'customer/bulk_import.html')
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
                    return render(request, 'customer/bulk_import.html')
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return render(request, 'customer/bulk_import.html')
            
            if not rows:
                messages.error(request, 'The file appears to be empty or has no data rows.')
                return render(request, 'customer/bulk_import.html')
            
            # Process rows and create customers
            success_count = 0
            error_count = 0
            errors = []
            
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
            
            for idx, row in enumerate(rows, start=2):  # Start from 2 (1 is header)
                try:
                    # Map CSV columns to model fields - handle None values and empty strings
                    # Headers are normalized to lowercase with underscores
                    
                    # Required fields (from add_customer_custom requirements)
                    site_name = row.get('site_name', '').strip() if row.get('site_name') else ''
                    mobile = row.get('mobile', '').strip() if row.get('mobile') else ''
                    job_no = row.get('job_no', '').strip() if row.get('job_no') else ''
                    city_value = row.get('city', '').strip() if row.get('city') else ''
                    
                    # Validate required fields (same as add_customer_custom)
                    if not site_name:
                        errors.append(f'Row {idx}: Site Name is required.')
                        error_count += 1
                        continue
                    
                    if not mobile:
                        errors.append(f'Row {idx}: Mobile is required.')
                        error_count += 1
                        continue
                    
                    # Validate mobile length (must be exactly 10 digits)
                    if len(mobile) != 10:
                        errors.append(f'Row {idx}: Mobile number must be exactly 10 digits.')
                        error_count += 1
                        continue
                    
                    if not job_no:
                        errors.append(f'Row {idx}: Job No is required.')
                        error_count += 1
                        continue
                    
                    # Check if job_no already exists (unique constraint)
                    if Customer.objects.filter(job_no=job_no).exists():
                        errors.append(f'Row {idx}: Job No "{job_no}" already exists.')
                        error_count += 1
                        continue
                    
                    if not city_value:
                        errors.append(f'Row {idx}: City is required.')
                        error_count += 1
                        continue
                    
                    # Get city by value
                    city = City.objects.filter(value=city_value).first()
                    if not city:
                        errors.append(f'Row {idx}: City "{city_value}" not found. Please use an existing city name.')
                        error_count += 1
                        continue
                    
                    # Optional fields
                    email = row.get('email', '').strip() if row.get('email') else ''
                    if email:
                        # Check if email already exists (unique constraint)
                        if Customer.objects.filter(email=email).exists():
                            errors.append(f'Row {idx}: Email "{email}" already exists.')
                            error_count += 1
                            continue
                    
                    phone = row.get('phone', '').strip() if row.get('phone') else ''
                    if phone:
                        # Validate phone length (must be exactly 10 digits if provided)
                        if len(phone) != 10:
                            errors.append(f'Row {idx}: Phone number must be exactly 10 digits.')
                            error_count += 1
                            continue
                        # Check if phone already exists (unique constraint)
                        if Customer.objects.filter(phone=phone).exists():
                            errors.append(f'Row {idx}: Phone "{phone}" already exists.')
                            error_count += 1
                            continue
                    
                    # Check if mobile already exists (unique constraint, but can be null)
                    if Customer.objects.filter(mobile=mobile).exists():
                        errors.append(f'Row {idx}: Mobile "{mobile}" already exists.')
                        error_count += 1
                        continue
                    
                    # Get foreign key objects
                    province_state = None
                    province_state_value = row.get('province_state', '').strip() if row.get('province_state') else ''
                    if province_state_value:
                        province_state = ProvinceState.objects.filter(value=province_state_value).first()
                        if not province_state:
                            errors.append(f'Row {idx}: Province/State "{province_state_value}" not found. Please use an existing province/state name.')
                            error_count += 1
                            continue
                    
                    routes = None
                    routes_value = row.get('routes', '').strip() if row.get('routes') else ''
                    if routes_value:
                        routes = Route.objects.filter(value=routes_value).first()
                        if not routes:
                            errors.append(f'Row {idx}: Route "{routes_value}" not found. Please use an existing route name.')
                            error_count += 1
                            continue
                    
                    branch = None
                    branch_value = row.get('branch', '').strip() if row.get('branch') else ''
                    if branch_value:
                        branch = Branch.objects.filter(value=branch_value).first()
                        if not branch:
                            errors.append(f'Row {idx}: Branch "{branch_value}" not found. Please use an existing branch name.')
                            error_count += 1
                            continue
                    
                    # Handle office address sync
                    site_address = row.get('site_address', '').strip() if row.get('site_address') else ''
                    office_address = row.get('office_address', '').strip() if row.get('office_address') else ''
                    same_as_site_address = row.get('same_as_site_address', '').strip() if row.get('same_as_site_address') else ''
                    # Convert to boolean
                    if isinstance(same_as_site_address, str):
                        same_as_site_address = same_as_site_address.lower() in ('true', 'on', '1', 'yes')
                    if same_as_site_address:
                        office_address = site_address
                    
                    # Handle dates
                    handover_date = None
                    handover_date_value = row.get('handover_date', '') or row.get('handover_date_str', '')
                    if handover_date_value:
                        handover_date = parse_date(handover_date_value)
                        if handover_date is None:
                            errors.append(f'Row {idx}: Invalid handover date format. Please use YYYY-MM-DD format.')
                            error_count += 1
                            continue
                    
                    # Handle latitude and longitude
                    latitude = None
                    longitude = None
                    latitude_value = row.get('latitude', '')
                    longitude_value = row.get('longitude', '')
                    if latitude_value:
                        try:
                            latitude = float(latitude_value)
                            if latitude < -90 or latitude > 90:
                                errors.append(f'Row {idx}: Latitude must be between -90 and 90 degrees.')
                                error_count += 1
                                continue
                        except (ValueError, TypeError):
                            latitude = None
                    
                    if longitude_value:
                        try:
                            longitude = float(longitude_value)
                            if longitude < -180 or longitude > 180:
                                errors.append(f'Row {idx}: Longitude must be between -180 and 180 degrees.')
                                error_count += 1
                                continue
                        except (ValueError, TypeError):
                            longitude = None
                    
                    # Other optional fields
                    contact_person_name = row.get('contact_person_name', '').strip() if row.get('contact_person_name') else ''
                    designation = row.get('designation', '').strip() if row.get('designation') else ''
                    pin_code = row.get('pin_code', '').strip() if row.get('pin_code') else ''
                    country = row.get('country', '').strip() if row.get('country') else ''
                    sector = row.get('sector', '').strip() if row.get('sector') else ''
                    if sector and sector not in ['government', 'private']:
                        sector = None
                    billing_name = row.get('billing_name', '').strip() if row.get('billing_name') else ''
                    notes = row.get('notes', '').strip() if row.get('notes') else ''
                    
                    # Handle generate_license_now (optional boolean)
                    generate_license_now = row.get('generate_license_now', '').strip() if row.get('generate_license_now') else ''
                    if isinstance(generate_license_now, str):
                        generate_license_now = generate_license_now.lower() in ('true', 'on', '1', 'yes')
                    else:
                        generate_license_now = False
                    
                    # Create customer (same structure as add_customer_custom)
                    customer = Customer.objects.create(
                        job_no=job_no,
                        site_name=site_name,
                        site_address=site_address,
                        email=email,
                        phone=phone,
                        mobile=mobile,
                        office_address=office_address,
                        same_as_site_address=same_as_site_address,
                        contact_person_name=contact_person_name,
                        designation=designation,
                        pin_code=pin_code,
                        province_state=province_state,
                        city=city,
                        sector=sector if sector else None,
                        routes=routes,
                        branch=branch,
                        handover_date=handover_date,
                        billing_name=billing_name,
                        generate_license_now=generate_license_now,
                        latitude=latitude,
                        longitude=longitude,
                        notes=notes,
                    )
                    
                    # Note: File uploads (uploads_files) cannot be handled in bulk import
                    # Users need to upload files individually after import
                    
                    # Validate and save (uses full_clean which applies all model validations)
                    try:
                        customer.full_clean()
                        customer.save()
                        success_count += 1
                    except ValidationError as e:
                        # Handle validation errors
                        if e.message_dict:
                            error_fields = ['site_name', 'mobile', 'job_no', 'city', 'email', 'phone']
                            error_msg = None
                            for field in error_fields:
                                if field in e.message_dict:
                                    error_msg = f"Row {idx}: {e.message_dict[field][0]}"
                                    break
                            if not error_msg:
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
                            errors.append(f'Row {idx}: Duplicate entry - {str(e)}')
                        else:
                            errors.append(f'Row {idx}: {str(e)}')
                        error_count += 1
                        continue
                        
                except Exception as e:
                    errors.append(f'Row {idx}: Unexpected error - {str(e)}')
                    error_count += 1
                    continue
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} customer(s).')
            if error_count > 0:
                error_message = f'Failed to import {error_count} row(s).'
                if errors:
                    error_message += ' Errors: ' + '; '.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f' ... and {len(errors) - 10} more error(s).'
                messages.error(request, error_message)
            
            return render(request, 'customer/bulk_import.html')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return render(request, 'customer/bulk_import.html')
    
    # GET request - render form
    return render(request, 'customer/bulk_import.html')
