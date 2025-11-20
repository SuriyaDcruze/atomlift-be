from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.widgets import SnippetListingButton
import json
from datetime import datetime

from .models import Customer, Route, Branch, ProvinceState, City, CustomerLicense, CustomerContact, CustomerFeedback, CustomerFollowUp


@hooks.register('register_admin_urls')
def register_customer_form_url():
    return [
        path('customer/add-custom/', add_customer_custom, name='add_customer_custom'),
        path('customer/edit-custom/<int:pk>/', edit_customer_custom, name='edit_customer_custom'),
        path('customer/view-custom/<int:pk>/', view_customer_custom, name='view_customer_custom'),
        # API endpoints for dropdown management
        path('api/customer/routes/', manage_routes, name='api_manage_routes'),
        path('api/customer/routes/<int:pk>/', manage_routes, name='api_manage_routes_detail'),
        path('api/customer/branches/', manage_branches, name='api_manage_branches'),
        path('api/customer/branches/<int:pk>/', manage_branches, name='api_manage_branches_detail'),
        path('api/customer/states/', manage_states, name='api_manage_states'),
        path('api/customer/states/<int:pk>/', manage_states, name='api_manage_states_detail'),
        path('api/customer/cities/', manage_cities, name='api_manage_cities'),
        path('api/customer/cities/<int:pk>/', manage_cities_detail, name='api_manage_cities_detail'),
        path('api/customer/contacts/create/', create_customer_contact, name='create_customer_contact'),
        path('api/customer/<int:customer_id>/notes/', update_customer_notes, name='update_customer_notes'),
        path('api/customer/feedback/create/', create_customer_feedback, name='create_customer_feedback'),
        path('api/customer/followup/create/', create_customer_followup, name='create_customer_followup'),
        # Customer License custom pages
        path('customer-license/add-custom/', add_customer_license_custom, name='add_customer_license_custom'),
        path('customer-license/edit-custom/<int:pk>/', edit_customer_license_custom, name='edit_customer_license_custom'),
        # API endpoints for customer license
        path('api/customer/<int:customer_id>/lifts/', get_customer_lifts, name='get_customer_lifts'),
        path('api/customer/<int:customer_id>/licenses/', get_customer_licenses, name='get_customer_licenses'),
        path('api/customer-license/customer/<int:customer_id>/', get_customer_for_license, name='get_customer_for_license'),
        path('api/customer-license/next-reference/', get_next_license_reference, name='get_next_license_reference'),
    ]


@hooks.register('construct_snippet_listing_buttons')
def customize_customer_listing_buttons(buttons, snippet, user, context=None):
    """Customize Customer listing buttons - remove default edit, add custom edit and view"""
    if isinstance(snippet, Customer):
        # Remove any default edit buttons
        buttons[:] = [btn for btn in buttons if not (hasattr(btn, 'label') and btn.label == 'Edit')]
        
        # Add custom buttons
        view_url = f"/admin/customer/view-custom/{snippet.pk}/"
        edit_url = f"/admin/customer/edit-custom/{snippet.pk}/"
        
        # Insert custom edit button at the beginning
        buttons.insert(0, SnippetListingButton(
            label='Edit',
            url=edit_url,
            priority=10,
            icon_name='edit',
        ))
        
        # Add custom view button
        buttons.append(SnippetListingButton(
            label='View',
            url=view_url,
            priority=90,
            icon_name='view',
        ))
    # CustomerLicense buttons are now enabled for manual editing
    # elif isinstance(snippet, CustomerLicense):
    #     # Remove all action buttons (Edit, Delete) for CustomerLicense
    #     buttons[:] = []
    
    return buttons


# @hooks.register('register_admin_menu_item')
# def register_customer_menu_item():
#     return MenuItem(
#         'Add Customer',
#         reverse('add_customer_custom'),
#         icon_name='user',
#         order=1000
#     )


def add_customer_custom(request):
    """Custom view for adding a customer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['site_name', 'mobile', 'job_no', 'city']  # site_id removed - don't need
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Validate mobile length
            mobile = data.get('mobile', '')
            if len(mobile) != 10:
                return JsonResponse({
                    'success': False,
                    'error': 'Mobile number must be exactly 10 digits'
                }, status=400)
            
            # Validate phone if provided
            phone = data.get('phone', '')
            if phone and len(phone) != 10:
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number must be exactly 10 digits'
                }, status=400)
            
            # Get foreign key objects
            province_state = None
            if data.get('province_state'):
                province_state = ProvinceState.objects.filter(id=data['province_state']).first()
            
            routes = None
            if data.get('routes'):
                routes = Route.objects.filter(id=data['routes']).first()
            
            branch = None
            if data.get('branch'):
                branch = Branch.objects.filter(id=data['branch']).first()
            
            city = None
            if data.get('city'):
                city = City.objects.filter(id=data['city']).first()
            
            # Handle office address sync
            office_address = data.get('office_address', '')
            same_as_site = data.get('same_as_site_address')
            if isinstance(same_as_site, str):
                same_as_site = same_as_site.lower() in ('true', 'on', '1')
            if same_as_site:
                office_address = data.get('site_address', '')

            # Generate customer license - commented out for now, will be used in future
            # generate_license = data.get('generate_customer_license')
            # if isinstance(generate_license, str):
            #     generate_license = generate_license.lower() in ('true', 'on', '1')
            generate_license = False

            # Handle latitude and longitude
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            if latitude == '' or latitude is None:
                latitude = None
            else:
                try:
                    latitude = float(latitude)
                except (ValueError, TypeError):
                    latitude = None
            
            if longitude == '' or longitude is None:
                longitude = None
            else:
                try:
                    longitude = float(longitude)
                except (ValueError, TypeError):
                    longitude = None

            # Create customer
            customer = Customer.objects.create(
                # site_id=data['site_id'],  # Don't need
                job_no=data.get('job_no', ''),
                site_name=data['site_name'],
                site_address=data.get('site_address', ''),
                email=data.get('email', ''),
                phone=phone,
                mobile=mobile,
                office_address=office_address,
                same_as_site_address=same_as_site,
                contact_person_name=data.get('contact_person_name', ''),
                designation=data.get('designation', ''),
                pin_code=data.get('pin_code', ''),
                province_state=province_state,
                city=city,
                sector=data.get('sector') if data.get('sector') else None,
                routes=routes,
                branch=branch,
                handover_date=data.get('handover_date') if data.get('handover_date') else None,
                billing_name=data.get('billing_name', ''),
                # Generate license now - commented out for now, will be used in future
                # generate_license_now=generate_license,
                latitude=latitude,
                longitude=longitude,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Customer created successfully',
                'customer': {
                    'id': customer.id,
                    'reference_id': customer.reference_id,
                    'site_name': customer.site_name,
                    'job_no': customer.job_no
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form
    context = {
        'is_edit': False,
        'routes': Route.objects.all(),
        'branches': Branch.objects.all(),
        'states': ProvinceState.objects.all(),
        'cities': City.objects.all(),
    }
    return render(request, 'customer/add_customer_custom.html', context)


def edit_customer_custom(request, pk):
    """Custom view for editing a customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['site_name', 'mobile', 'job_no', 'city']  # site_id removed - don't need
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Update fields
            # customer.site_id = data.get('site_id', customer.site_id)  # Don't need
            customer.job_no = data.get('job_no', customer.job_no)
            customer.site_name = data.get('site_name', customer.site_name)
            customer.site_address = data.get('site_address', customer.site_address)
            customer.email = data.get('email', customer.email)
            customer.phone = data.get('phone', customer.phone)
            customer.mobile = data.get('mobile', customer.mobile)
            customer.same_as_site_address = data.get('same_as_site_address', False)
            
            # Handle office address
            if customer.same_as_site_address:
                customer.office_address = customer.site_address
            else:
                customer.office_address = data.get('office_address', customer.office_address)
            
            customer.contact_person_name = data.get('contact_person_name', customer.contact_person_name)
            customer.designation = data.get('designation', customer.designation)
            customer.pin_code = data.get('pin_code', customer.pin_code)
            if data.get('city'):
                customer.city = City.objects.filter(id=data['city']).first()
            customer.sector = data.get('sector') if data.get('sector') else customer.sector
            customer.billing_name = data.get('billing_name', customer.billing_name)
            
            # Handle latitude and longitude
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            if latitude == '' or latitude is None:
                customer.latitude = None
            else:
                try:
                    customer.latitude = float(latitude)
                except (ValueError, TypeError):
                    customer.latitude = None
            
            if longitude == '' or longitude is None:
                customer.longitude = None
            else:
                try:
                    customer.longitude = float(longitude)
                except (ValueError, TypeError):
                    customer.longitude = None
            
            # Update foreign keys
            if data.get('province_state'):
                customer.province_state = ProvinceState.objects.filter(id=data['province_state']).first()
            
            if data.get('routes'):
                customer.routes = Route.objects.filter(id=data['routes']).first()
            
            if data.get('branch'):
                customer.branch = Branch.objects.filter(id=data['branch']).first()
            
            if data.get('handover_date'):
                customer.handover_date = data['handover_date']
            
            customer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Customer updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form with same template as add (uses is_edit flag)
    context = {
        'is_edit': True,
        'customer': customer,
        'routes': Route.objects.all(),
        'branches': Branch.objects.all(),
        'states': ProvinceState.objects.all(),
        'cities': City.objects.all(),
    }
    return render(request, 'customer/add_customer_custom.html', context)


def view_customer_custom(request, pk):
    """Custom view for viewing customer details in read-only mode"""
    from lift.models import Lift
    from invoice.models import Invoice
    from amc.models import AMC
    from PaymentReceived.models import PaymentReceived
    from Routine_services.models import RoutineService
    from complaints.models import Complaint
    
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get lifts assigned to this customer (where lift_code equals customer's job_no)
    lifts = []
    if customer.job_no:
        lifts = Lift.objects.filter(lift_code=customer.job_no)
    
    # Get invoices for this customer
    invoices = Invoice.objects.filter(customer=customer).select_related('customer').prefetch_related('items').order_by('-start_date')
    
    # Get AMCs for this customer
    try:
        amcs = AMC.objects.filter(customer=customer).order_by('-start_date')
    except:
        amcs = []
    
    # Get payments for this customer (field is 'date' not 'payment_date')
    try:
        payments = PaymentReceived.objects.filter(customer=customer).order_by('-date')
    except:
        payments = []
    
    # Get routine services for this customer
    try:
        routine_services = RoutineService.objects.filter(customer=customer).order_by('-id')
    except:
        routine_services = []
    
    # Get complaints for this customer
    try:
        complaints = Complaint.objects.filter(customer=customer).order_by('-date')
    except:
        complaints = []
    
    # Get feedbacks for this customer
    feedbacks = CustomerFeedback.objects.filter(customer=customer).order_by('-created_date')
    
    # Get follow-ups for this customer
    follow_ups = CustomerFollowUp.objects.filter(customer=customer).select_related('contact').order_by('-follow_up_date', '-created_date')
    
    # Get contacts for this customer
    contacts = CustomerContact.objects.filter(customer=customer).order_by('first_name', 'last_name')
    
    context = {
        'customer': customer,
        'lifts': lifts,
        'invoices': invoices,
        'amcs': amcs,
        'payments': payments,
        'routine_services': routine_services,
        'complaints': complaints,
        'feedbacks': feedbacks,
        'follow_ups': follow_ups,
        'contacts': contacts,
    }
    return render(request, 'customer/view_customer_custom.html', context)


# API endpoints for dropdown management
@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_routes(request, pk=None):
    """API for managing routes"""
    if request.method == 'GET':
        routes = Route.objects.all().values('id', 'value')
        return JsonResponse(list(routes), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            route = Route.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': route.id,
                'value': route.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_routes(request, pk):
    """API for updating/deleting routes"""
    try:
        route = get_object_or_404(Route, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            route.value = data['value']
            route.save()
            return JsonResponse({'success': True, 'message': 'Route updated'})
        
        elif request.method == 'DELETE':
            route.delete()
            return JsonResponse({'success': True, 'message': 'Route deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_branches(request, pk=None):
    """API for managing branches"""
    if request.method == 'GET':
        branches = Branch.objects.all().values('id', 'value')
        return JsonResponse(list(branches), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            branch = Branch.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': branch.id,
                'value': branch.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_branches(request, pk):
    """API for updating/deleting branches"""
    try:
        branch = get_object_or_404(Branch, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            branch.value = data['value']
            branch.save()
            return JsonResponse({'success': True, 'message': 'Branch updated'})
        
        elif request.method == 'DELETE':
            branch.delete()
            return JsonResponse({'success': True, 'message': 'Branch deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_states(request, pk=None):
    """API for managing states"""
    if request.method == 'GET':
        states = ProvinceState.objects.all().values('id', 'value')
        return JsonResponse(list(states), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            state = ProvinceState.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': state.id,
                'value': state.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_states(request, pk):
    """API for updating/deleting states"""
    try:
        state = get_object_or_404(ProvinceState, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            state.value = data['value']
            state.save()
            return JsonResponse({'success': True, 'message': 'State updated'})
        
        elif request.method == 'DELETE':
            state.delete()
            return JsonResponse({'success': True, 'message': 'State deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_cities(request, pk=None):
    """API for managing cities"""
    if request.method == 'GET':
        cities = City.objects.all().values('id', 'value')
        return JsonResponse(list(cities), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            city = City.objects.create(value=data['value'])
            return JsonResponse({
                'success': True,
                'id': city.id,
                'value': city.value
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_cities_detail(request, pk):
    """API for updating/deleting cities"""
    try:
        city = get_object_or_404(City, pk=pk)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            city.value = data['value']
            city.save()
            return JsonResponse({'success': True, 'message': 'City updated'})
        
        elif request.method == 'DELETE':
            city.delete()
            return JsonResponse({'success': True, 'message': 'City deleted'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def create_customer_contact(request):
    """API endpoint to create a customer contact"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        customer_id = data.get('customer_id')
        first_name = data.get('first_name', '').strip()
        
        if not customer_id:
            return JsonResponse({
                'success': False,
                'error': 'Customer ID is required'
            }, status=400)
        
        if not first_name:
            return JsonResponse({
                'success': False,
                'error': 'First name is required'
            }, status=400)
        
        # Get customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Customer not found'
            }, status=404)
        
        # Create contact
        contact = CustomerContact.objects.create(
            customer=customer,
            first_name=first_name,
            last_name=data.get('last_name', '').strip() or None,
            email=data.get('email', '').strip() or None,
            phone=data.get('phone', '').strip() or None,
            mobile=data.get('mobile', '').strip() or None,
            designation=data.get('designation', '').strip() or None,
            address=data.get('address', '').strip() or None,
            pin_code=data.get('pin_code', '').strip() or None,
            city=data.get('city', '').strip() or None,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Contact created successfully',
            'contact': {
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email': contact.email,
                'phone': contact.phone,
                'mobile': contact.mobile,
                'designation': contact.designation,
                'city': contact.city,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def update_customer_notes(request, customer_id):
    """API endpoint to update customer notes"""
    try:
        # Get customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Customer not found'
            }, status=404)
        
        # Get notes from request
        data = json.loads(request.body)
        notes = data.get('notes', '').strip()
        
        # Update notes
        customer.notes = notes
        customer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notes updated successfully',
            'notes': customer.notes or ''
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_customer_feedback(request):
    """API endpoint to create customer feedback"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        customer_id = data.get('customer_id')
        rating = data.get('rating', 0)
        
        if not customer_id:
            return JsonResponse({
                'success': False,
                'error': 'Customer ID is required'
            }, status=400)
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 0 or rating > 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Rating must be between 0 and 5'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Rating must be a number'
            }, status=400)
        
        # Get customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Customer not found'
            }, status=404)
        
        # Create feedback
        feedback = CustomerFeedback.objects.create(
            customer=customer,
            rating=rating,
            friendliness=data.get('friendliness') or None,
            knowledge=data.get('knowledge') or None,
            quickness=data.get('quickness') or None,
            review=data.get('review', '').strip() or None,
            improvement_suggestion=data.get('improvement_suggestion', '').strip() or None,
            status=data.get('status', 'pending'),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Feedback created successfully',
            'feedback': {
                'id': feedback.id,
                'feedback_id': feedback.feedback_id,
                'rating': feedback.rating,
                'created_date': feedback.created_date.strftime('%Y-%m-%d'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_customer_followup(request):
    """API endpoint to create customer follow-up"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        customer_id = data.get('customer_id')
        follow_up_date = data.get('follow_up_date')
        contact_id = data.get('contact_id')
        
        if not customer_id:
            return JsonResponse({
                'success': False,
                'error': 'Customer ID is required'
            }, status=400)
        
        if not follow_up_date:
            return JsonResponse({
                'success': False,
                'error': 'Follow-up date is required'
            }, status=400)
        
        # Get customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Customer not found'
            }, status=404)
        
        # Get contact if provided
        contact = None
        if contact_id:
            # Handle empty string or None
            contact_id_str = str(contact_id).strip()
            if contact_id_str and contact_id_str != '' and contact_id_str.lower() != 'null':
                try:
                    contact = CustomerContact.objects.get(pk=int(contact_id_str), customer=customer)
                except (CustomerContact.DoesNotExist, ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'Contact not found'
                    }, status=404)
        
        # Parse the date string
        from datetime import datetime
        from django.utils.dateparse import parse_date
        try:
            # Try to parse the date string (format: YYYY-MM-DD)
            if isinstance(follow_up_date, str):
                parsed_date = parse_date(follow_up_date)
                if parsed_date is None:
                    # Fallback to datetime.strptime
                    parsed_date = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
            elif hasattr(follow_up_date, 'date'):
                # It's a datetime object, convert to date
                parsed_date = follow_up_date.date()
            else:
                # Already a date object
                parsed_date = follow_up_date
        except (ValueError, TypeError, AttributeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid date format. Expected YYYY-MM-DD, got: {follow_up_date} (type: {type(follow_up_date).__name__})'
            }, status=400)
        
        # Create follow-up
        try:
            followup = CustomerFollowUp.objects.create(
                customer=customer,
                follow_up_date=parsed_date,
                contact=contact,
                comment=data.get('comment', '').strip() or None,
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return JsonResponse({
                'success': False,
                'error': f'Failed to create follow-up: {str(e)}',
                'traceback': error_details
            }, status=400)
        
        # Format the date safely for JSON response
        try:
            if hasattr(followup.follow_up_date, 'strftime'):
                follow_up_date_str = followup.follow_up_date.strftime('%Y-%m-%d')
            elif hasattr(followup.follow_up_date, 'isoformat'):
                follow_up_date_str = followup.follow_up_date.isoformat()
            else:
                follow_up_date_str = str(followup.follow_up_date)
        except Exception as e:
            follow_up_date_str = str(followup.follow_up_date)
        
        return JsonResponse({
            'success': True,
            'message': 'Follow-up created successfully',
            'followup': {
                'id': followup.id,
                'followup_id': followup.followup_id,
                'follow_up_date': follow_up_date_str,
                'contact_name': f"{followup.contact.first_name} {followup.contact.last_name or ''}".strip() if followup.contact else None,
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': error_details
        }, status=500)


# ======================================================
#  CUSTOMER LICENSE CUSTOM VIEWS
# ======================================================

def add_customer_license_custom(request):
    """Custom view for adding a customer license"""
    from datetime import date, timedelta
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['customer', 'lift', 'period_start', 'period_end']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Get foreign key objects
            customer = None
            if data.get('customer'):
                customer = Customer.objects.filter(id=data['customer']).first()
                if not customer:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid customer selected'
                    }, status=400)
            
            lift = None
            if data.get('lift'):
                from lift.models import Lift
                lift = Lift.objects.filter(id=data['lift']).first()
                if not lift:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid lift selected'
                    }, status=400)
            
            # Validate dates
            period_start = data.get('period_start')
            period_end = data.get('period_end')
            
            if period_start and period_end:
                try:
                    start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
                    if start_date >= end_date:
                        return JsonResponse({
                            'success': False,
                            'error': 'Start date must be before end date.'
                        }, status=400)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid date format. Please use YYYY-MM-DD format.'
                    }, status=400)
            
            # Get government license number (optional, unique)
            government_license_no = data.get('license_no', '').strip() or None
            
            # Validate government license number uniqueness if provided
            if government_license_no:
                if CustomerLicense.objects.filter(license_no=government_license_no).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Government license number already exists. Please enter a different number.'
                    }, status=400)
            
            # Get status
            status = data.get('status', 'active')
            if status not in ['active', 'expired']:
                status = 'active'
            
            # Create customer license (license_ref_no will be auto-generated by model)
            license_obj = CustomerLicense.objects.create(
                license_ref_no='',  # Empty string - will be auto-generated by model's save() method
                license_no=government_license_no,  # Government-issued license number
                customer=customer,
                lift=lift,
                period_start=period_start,
                period_end=period_end,
                status=status,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Customer license created successfully',
                'license': {
                    'id': license_obj.id,
                    'license_ref_no': license_obj.license_ref_no,
                    'license_no': license_obj.license_no or '',
                    'customer': license_obj.customer.site_name,
                    'lift': license_obj.lift.lift_code
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form
    customers = Customer.objects.all().order_by('site_name')
    from lift.models import Lift
    lifts = Lift.objects.all().order_by('lift_code')
    
    context = {
        'is_edit': False,
        'customers': customers,
        'lifts': lifts,
    }
    return render(request, 'customer/add_customer_license_custom.html', context)


def edit_customer_license_custom(request, pk):
    """Custom view for editing a customer license"""
    license_obj = get_object_or_404(CustomerLicense, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['customer', 'lift', 'period_start', 'period_end']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Get foreign key objects
            customer = None
            if data.get('customer'):
                customer = Customer.objects.filter(id=data['customer']).first()
                if not customer:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid customer selected'
                    }, status=400)
            
            lift = None
            if data.get('lift'):
                from lift.models import Lift
                lift = Lift.objects.filter(id=data['lift']).first()
                if not lift:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid lift selected'
                    }, status=400)
            
            # Validate dates
            period_start = data.get('period_start')
            period_end = data.get('period_end')
            
            if period_start and period_end:
                try:
                    start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
                    if start_date >= end_date:
                        return JsonResponse({
                            'success': False,
                            'error': 'Start date must be before end date.'
                        }, status=400)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid date format. Please use YYYY-MM-DD format.'
                    }, status=400)
            
            # Get government license number
            government_license_no = data.get('license_no', '').strip() or None
            
            # Validate government license number uniqueness if changed
            if government_license_no and government_license_no != (license_obj.license_no or ''):
                if CustomerLicense.objects.filter(license_no=government_license_no).exclude(pk=license_obj.pk).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Government license number already exists. Please enter a different number.'
                    }, status=400)
            
            # Get status
            status = data.get('status', license_obj.status)
            if status not in ['active', 'expired']:
                status = license_obj.status
            
            # Update license (license_ref_no is read-only, don't change it)
            license_obj.license_no = government_license_no
            license_obj.customer = customer
            license_obj.lift = lift
            license_obj.period_start = period_start
            license_obj.period_end = period_end
            license_obj.status = status
            license_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Customer license updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render form with existing data
    customers = Customer.objects.all().order_by('site_name')
    from lift.models import Lift
    lifts = Lift.objects.all().order_by('lift_code')
    
    context = {
        'is_edit': True,
        'license': license_obj,
        'customers': customers,
        'lifts': lifts,
    }
    return render(request, 'customer/add_customer_license_custom.html', context)


# ======================================================
#  CUSTOMER LICENSE API ENDPOINTS
# ======================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_customer_lifts(request, customer_id):
    """Get lifts associated with a customer through licenses"""
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        from lift.models import Lift
        
        lifts_data = []
        lift_ids = set()
        assigned_lift_id = None
        
        # Priority 1: Find lift matching customer's job_no (this is the primary assigned lift)
        if customer.job_no:
            matching_lift = Lift.objects.filter(lift_code=customer.job_no).first()
            if matching_lift:
                assigned_lift_id = matching_lift.id
                lift_ids.add(matching_lift.id)
                # Add matching lift first (at the beginning of the list)
                lifts_data.insert(0, {
                    'id': matching_lift.id,
                    'lift_code': matching_lift.lift_code or '',
                    'name': matching_lift.name or '',
                    'reference_id': matching_lift.reference_id or '',
                })
        
        # Priority 2: Get lifts that have licenses for this customer
        licenses = CustomerLicense.objects.filter(customer=customer).select_related('lift')
        for license_obj in licenses:
            if license_obj.lift and license_obj.lift.id not in lift_ids:
                lift = license_obj.lift
                lift_ids.add(lift.id)
                lifts_data.append({
                    'id': lift.id,
                    'lift_code': lift.lift_code or '',
                    'name': lift.name or '',
                    'reference_id': lift.reference_id or '',
                })
        
        # If no lifts found, return all lifts (so user can still select)
        if not lifts_data:
            all_lifts = Lift.objects.all().order_by('lift_code')
            for lift in all_lifts:
                lifts_data.append({
                    'id': lift.id,
                    'lift_code': lift.lift_code or '',
                    'name': lift.name or '',
                    'reference_id': lift.reference_id or '',
                })
        
        return JsonResponse({
            'success': True,
            'lifts': lifts_data,
            'assigned_lift_id': assigned_lift_id,  # The lift matching job_no
            'customer_job_no': customer.job_no or ''  # Customer's job_no for reference
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_customer_licenses(request, customer_id):
    """Get all licenses for a customer"""
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        licenses = CustomerLicense.objects.filter(customer=customer).select_related('lift').order_by('-period_start')
        
        licenses_data = []
        for license_obj in licenses:
            licenses_data.append({
                'id': license_obj.id,
                'license_ref_no': license_obj.license_ref_no,
                'license_no': license_obj.license_no or '',
                'lift_code': license_obj.lift.lift_code if license_obj.lift else 'N/A',
                'lift_name': license_obj.lift.name if license_obj.lift else 'N/A',
                'period_start': license_obj.period_start.strftime('%Y-%m-%d') if license_obj.period_start else '',
                'period_end': license_obj.period_end.strftime('%Y-%m-%d') if license_obj.period_end else '',
                'status': license_obj.status,
                'status_display': license_obj.get_status_display(),
            })
        
        return JsonResponse({
            'success': True,
            'licenses': licenses_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_customer_for_license(request, customer_id):
    """Get customer details with assigned lift for license form (similar to AMC pattern)"""
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        from lift.models import Lift
        
        # Find assigned lift - priority: 1) Lift matching job_no, 2) First lift from licenses
        assigned_lift_id = None
        assigned_lift_code = None
        assigned_lift_name = None
        
        if customer.job_no:
            matching_lift = Lift.objects.filter(lift_code=customer.job_no).first()
            if matching_lift:
                assigned_lift_id = matching_lift.id
                assigned_lift_code = matching_lift.lift_code
                assigned_lift_name = matching_lift.name
        
        # If no matching lift by job_no, use first lift from licenses
        if not assigned_lift_id:
            licenses = CustomerLicense.objects.filter(customer=customer).select_related('lift').first()
            if licenses and licenses.lift:
                assigned_lift_id = licenses.lift.id
                assigned_lift_code = licenses.lift.lift_code
                assigned_lift_name = licenses.lift.name
        
        return JsonResponse({
            'id': customer.id,
            'reference_id': customer.reference_id,
            'site_name': customer.site_name,
            'job_no': customer.job_no or '',
            'assigned_lift_id': assigned_lift_id,
            'assigned_lift_code': assigned_lift_code or '',
            'assigned_lift_name': assigned_lift_name or '',
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_next_license_reference(request):
    """Get the next license reference ID (e.g., LIC0001, LIC0002)"""
    try:
        # Get all licenses with license_ref_no starting with "LIC"
        licenses = CustomerLicense.objects.filter(license_ref_no__startswith="LIC").exclude(license_ref_no="")
        
        if licenses.exists():
            # Extract numbers from all license_ref_no values and find the maximum
            max_id = 0
            for license_obj in licenses:
                if license_obj.license_ref_no and license_obj.license_ref_no.startswith("LIC"):
                    try:
                        # Extract number from "LIC0001" -> 1
                        num_str = license_obj.license_ref_no.replace("LIC", "").lstrip("0")
                        if num_str:  # If there's a number after removing zeros
                            num = int(num_str)
                            max_id = max(max_id, num)
                        else:
                            # Handle case like "LIC0000" -> 0
                            max_id = max(max_id, 0)
                    except (ValueError, AttributeError):
                        continue
            next_id = max_id + 1
        else:
            next_id = 1
        
        next_ref = f"LIC{next_id:04d}"
        return JsonResponse({"reference_id": next_ref})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
