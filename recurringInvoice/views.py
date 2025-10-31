import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import RecurringInvoice
from customer.models import Customer
from authentication.models import CustomUser


def add_recurring_invoice_custom(request):
    """Custom add recurring invoice page"""
    context = {
        'customers': Customer.objects.all().order_by('site_name'),
        'users': CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username'),
        'is_edit': False,
    }
    return render(request, 'recurringInvoice/add_recurring_invoice_custom.html', context)


def edit_recurring_invoice_custom(request, reference_id):
    """Custom edit recurring invoice page"""
    recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
    context = {
        'recurring_invoice': recurring_invoice,
        'customers': Customer.objects.all().order_by('site_name'),
        'users': CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username'),
        'is_edit': True,
    }
    return render(request, 'recurringInvoice/edit_recurring_invoice_custom.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_recurring_invoice(request):
    """Create a new recurring invoice"""
    try:
        data = request.POST
        
        # Get customer
        customer_id = data.get('customer')
        if not customer_id:
            return JsonResponse({"success": False, "error": "Customer is required"}, status=400)
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get sales person if provided
        sales_person = None
        if data.get('sales_person'):
            sales_person = get_object_or_404(CustomUser, id=data.get('sales_person'))
        
        # Create recurring invoice
        recurring_invoice = RecurringInvoice.objects.create(
            customer=customer,
            profile_name=data.get('profile_name', ''),
            order_number=data.get('order_number', ''),
            repeat_every=data.get('repeat_every', 'month'),
            auto_repeat='auto_repeat' in data and (data.get('auto_repeat') == 'on' or data.get('auto_repeat') == 'true' or data.get('auto_repeat') == True),
            start_date=data.get('start_date'),
            end_date=data.get('end_date') if data.get('end_date') else None,
            sales_person=sales_person,
            billing_address=data.get('billing_address', ''),
            gst_treatment=data.get('gst_treatment', ''),
            status=data.get('status', 'active'),
        )
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            recurring_invoice.uploads_files = request.FILES['uploads_files']
            recurring_invoice.save()
        
        # Handle items
        from .models import RecurringInvoiceItem
        from items.models import Item
        items_json = data.get('items', '[]')
        items_created = 0
        try:
            items_data = json.loads(items_json)
            for item_data in items_data:
                try:
                    item_id = item_data.get('item')
                    if item_id:  # Only create if item is selected
                        # Verify the item exists before creating
                        try:
                            item_obj = Item.objects.get(id=int(item_id))
                        except Item.DoesNotExist:
                            print(f"Item with id {item_id} does not exist, skipping")
                            continue
                        
                        RecurringInvoiceItem.objects.create(
                            recurring_invoice=recurring_invoice,
                            item=item_obj,
                            rate=float(item_data.get('rate', 0)),
                            qty=int(item_data.get('qty', 1)),
                            tax=float(item_data.get('tax', 0))
                        )
                        items_created += 1
                except (ValueError, TypeError) as e:
                    print(f"Error creating item: {e}, data: {item_data}")
                    continue  # Skip invalid items
        except json.JSONDecodeError as e:
            print(f"Error parsing items JSON: {e}")
        
        message = f"Recurring Invoice {recurring_invoice.reference_id} created successfully"
        if items_created > 0:
            message += f" with {items_created} item(s)"
        
        return JsonResponse({
            "success": True,
            "message": message
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating recurring invoice: {error_details}")
        return JsonResponse({"success": False, "error": f"Error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_recurring_invoice(request, reference_id):
    """Update an existing recurring invoice"""
    try:
        recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
        data = request.POST
        
        # Update customer
        if data.get('customer'):
            customer = get_object_or_404(Customer, id=data.get('customer'))
            recurring_invoice.customer = customer
        
        # Update sales person
        if data.get('sales_person'):
            sales_person = get_object_or_404(CustomUser, id=data.get('sales_person'))
            recurring_invoice.sales_person = sales_person
        else:
            recurring_invoice.sales_person = None
        
        # Update other fields
        recurring_invoice.profile_name = data.get('profile_name', recurring_invoice.profile_name)
        recurring_invoice.order_number = data.get('order_number', recurring_invoice.order_number)
        recurring_invoice.repeat_every = data.get('repeat_every', recurring_invoice.repeat_every)
        recurring_invoice.auto_repeat = 'auto_repeat' in data and (data.get('auto_repeat') == 'on' or data.get('auto_repeat') == 'true' or data.get('auto_repeat') == True)
        recurring_invoice.start_date = data.get('start_date', recurring_invoice.start_date)
        recurring_invoice.end_date = data.get('end_date') if data.get('end_date') else None
        recurring_invoice.billing_address = data.get('billing_address', recurring_invoice.billing_address)
        recurring_invoice.gst_treatment = data.get('gst_treatment', recurring_invoice.gst_treatment)
        recurring_invoice.status = data.get('status', recurring_invoice.status)
        
        # Handle file upload
        if 'uploads_files' in request.FILES:
            recurring_invoice.uploads_files = request.FILES['uploads_files']
        
        recurring_invoice.save()
        
        # Handle items - clear existing and add new ones
        from .models import RecurringInvoiceItem
        from items.models import Item
        items_json = data.get('items', '[]')
        items_created = 0
        try:
            items_data = json.loads(items_json)
            # Clear existing items
            recurring_invoice.items.all().delete()
            # Add new items
            for item_data in items_data:
                try:
                    item_id = item_data.get('item')
                    if item_id:  # Only create if item is selected
                        # Verify the item exists before creating
                        try:
                            item_obj = Item.objects.get(id=int(item_id))
                        except Item.DoesNotExist:
                            print(f"Item with id {item_id} does not exist, skipping")
                            continue
                        
                        RecurringInvoiceItem.objects.create(
                            recurring_invoice=recurring_invoice,
                            item=item_obj,
                            rate=float(item_data.get('rate', 0)),
                            qty=int(item_data.get('qty', 1)),
                            tax=float(item_data.get('tax', 0))
                        )
                        items_created += 1
                except (ValueError, TypeError) as e:
                    print(f"Error creating item: {e}, data: {item_data}")
                    continue  # Skip invalid items
        except json.JSONDecodeError as e:
            print(f"Error parsing items JSON: {e}")
        
        message = f"Recurring Invoice {recurring_invoice.reference_id} updated successfully"
        if items_created > 0:
            message += f" with {items_created} item(s)"
        
        return JsonResponse({
            "success": True,
            "message": message
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error updating recurring invoice: {error_details}")
        return JsonResponse({"success": False, "error": f"Error: {str(e)}"}, status=500)


# API endpoints for fetching dropdown options
@require_http_methods(["GET"])
def get_customers(request):
    """Get all customers"""
    try:
        customers = Customer.objects.all().order_by('site_name')
        data = [
            {
                "id": customer.id, 
                "site_name": customer.site_name,
                "site_address": customer.site_address,
                "office_address": customer.office_address,
                "job_no": customer.job_no,
                "site_id": customer.site_id,
                "reference_id": customer.reference_id,
                "email": customer.email,
                "phone": customer.phone
            }
            for customer in customers
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_recurring_invoices(request):
    """Get existing recurring invoices (minimal data for computing next reference id)"""
    try:
        recurring_invoices = RecurringInvoice.objects.all().only("reference_id").order_by("id")
        data = [
            {"reference_id": recurring_invoice.reference_id}
            for recurring_invoice in recurring_invoices
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_sales_persons(request):
    """Get all sales persons"""
    try:
        sales_persons = CustomUser.objects.filter(groups__name='employee').order_by('first_name', 'last_name', 'username')
        data = []
        for user in sales_persons:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            data.append({"id": user.id, "username": user.username, "name": full_name})
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_items(request):
    """Get all items"""
    try:
        from items.models import Item
        items = Item.objects.all().order_by('name')
        data = [
            {"id": item.id, "name": item.name, "sale_price": str(item.sale_price)}
            for item in items
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_recurring_invoice_items(request, reference_id):
    """Get items for a specific recurring invoice"""
    try:
        recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
        items = recurring_invoice.items.all().select_related('item')
        data = []
        
        for item in items:
            try:
                # Build item data safely
                item_data = {
                    "id": item.id,
                    "rate": str(item.rate),
                    "qty": item.qty,
                    "tax": str(item.tax),
                    "total": str(item.total)
                }
                
                # Handle the item relationship safely
                if item.item:
                    if hasattr(item.item, 'id') and hasattr(item.item, 'name'):
                        item_data["item"] = {
                            "id": item.item.id, 
                            "name": str(item.item.name)
                        }
                    else:
                        item_data["item"] = None
                else:
                    item_data["item"] = None
                
                data.append(item_data)
            except Exception as e:
                print(f"Error serializing item {item.id}: {e}")
                continue  # Skip items that can't be serialized
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        print(f"Error getting recurring invoice items: {traceback.format_exc()}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_renewal_status(request, reference_id):
    """Get renewal status for a specific recurring invoice"""
    try:
        recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
        renewal_info = recurring_invoice.get_renewal_info()
        
        return JsonResponse({
            "success": True,
            "renewal_info": renewal_info
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def renew_recurring_invoice(request, reference_id):
    """Renew a recurring invoice by extending its end date"""
    try:
        recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
        
        # Check if renewal is possible
        if not recurring_invoice.can_renew():
            return JsonResponse({
                "success": False, 
                "error": "This recurring invoice cannot be renewed. Check if it's active and has an end date."
            }, status=400)
        
        # Get renewal parameters from request
        data = request.POST if request.POST else {}
        extend_days = data.get('extend_days')
        new_end_date = data.get('new_end_date')
        
        # Validate parameters
        if extend_days:
            try:
                extend_days = int(extend_days)
                if extend_days <= 0:
                    raise ValueError("Extension days must be positive")
            except ValueError as e:
                return JsonResponse({
                    "success": False, 
                    "error": f"Invalid extension days: {str(e)}"
                }, status=400)
        
        if new_end_date:
            try:
                from datetime import datetime
                new_end_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
                if new_end_date <= recurring_invoice.end_date:
                    return JsonResponse({
                        "success": False, 
                        "error": "New end date must be after current end date"
                    }, status=400)
            except ValueError as e:
                return JsonResponse({
                    "success": False, 
                    "error": f"Invalid date format: {str(e)}"
                }, status=400)
        
        # Perform renewal
        old_end_date = recurring_invoice.end_date
        success = recurring_invoice.renew_recurring_invoice(
            new_end_date=new_end_date,
            extend_days=extend_days
        )
        
        if success:
            return JsonResponse({
                "success": True,
                "message": f"Recurring invoice {reference_id} renewed successfully",
                "old_end_date": old_end_date.strftime('%Y-%m-%d'),
                "new_end_date": recurring_invoice.end_date.strftime('%Y-%m-%d'),
                "renewal_info": recurring_invoice.get_renewal_info()
            })
        else:
            return JsonResponse({
                "success": False, 
                "error": "Failed to renew recurring invoice"
            }, status=500)
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error renewing recurring invoice: {error_details}")
        return JsonResponse({"success": False, "error": f"Error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def test_renewal(request):
    """Test page to verify renewal functionality"""
    try:
        from django.utils import timezone
        recurring_invoices = RecurringInvoice.objects.all()[:5]
        test_data = []
        
        for invoice in recurring_invoices:
            renewal_info = invoice.get_renewal_info()
            test_data.append({
                'reference_id': invoice.reference_id,
                'end_date': invoice.end_date,
                'status': invoice.status,
                'renewal_info': renewal_info
            })
        
        return JsonResponse({
            "success": True,
            "test_data": test_data,
            "current_date": timezone.now().date().strftime('%Y-%m-%d')
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def renew_recurring_invoice_direct(request, reference_id):
    """Direct renewal page for recurring invoice"""
    try:
        recurring_invoice = get_object_or_404(RecurringInvoice, reference_id=reference_id)
        
        if request.method == 'POST':
            # Get renewal parameters
            renewal_option = request.POST.get('renewal_option', 'default')
            extend_days = request.POST.get('extend_days')
            new_end_date = request.POST.get('new_end_date')
            
            # Process renewal based on option
            if renewal_option == 'custom' and extend_days:
                extend_days = int(extend_days)
                new_end_date = None
            elif renewal_option == 'date' and new_end_date:
                extend_days = None
            else:
                # Default option - extend by same period
                extend_days = None
                new_end_date = None
            
            # Perform renewal
            old_end_date = recurring_invoice.end_date
            success = recurring_invoice.renew_recurring_invoice(
                new_end_date=new_end_date,
                extend_days=extend_days
            )
            
            if success:
                messages.success(request, f'Recurring invoice {reference_id} renewed successfully! New end date: {recurring_invoice.end_date}')
                return redirect('/admin/snippets/recurringInvoice/recurringinvoice/')
            else:
                messages.error(request, 'Failed to renew recurring invoice.')
        
        # GET request - show renewal form
        renewal_info = recurring_invoice.get_renewal_info()
        
        context = {
            'instance': recurring_invoice,
            'renewal_info': renewal_info,
            'title': f'Renew {recurring_invoice.reference_id}',
        }
        
        return render(request, 'recurringInvoice/renew_modal.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('/admin/snippets/recurringInvoice/recurringinvoice/')