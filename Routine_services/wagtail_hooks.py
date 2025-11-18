from wagtail import hooks
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
import json

from .models import RoutineService
from amc.models import AMCRoutineService


# Hide Routine Service expiring viewsets from main menu (they're in Snippets menu)
@hooks.register('construct_main_menu')
def hide_routine_service_expiring_menu_items(request, menu_items):
    """Hide Routine Service expiring menu items from the admin menu (they're in Snippets)"""
    # Hidden menu labels for Routine Service expiring viewsets
    hidden_labels = [
        'This Month Expiring',
        'Last Month Expired',
        'Routine Services Expiring'
    ]
    
    new_menu_items = []
    for item in menu_items:
        # Check if this is a group and filter its submenu items
        if hasattr(item, 'menu_items') and item.menu_items:
            # Filter submenu items
            filtered_submenu = []
            for sub_item in item.menu_items:
                # Check by label or name
                item_label = getattr(sub_item, 'label', '') or getattr(sub_item, 'name', '')
                if item_label not in hidden_labels:
                    filtered_submenu.append(sub_item)
            # Update the submenu if it changed
            if len(filtered_submenu) != len(item.menu_items):
                item.menu_items = filtered_submenu
        # Check if this item itself should be hidden
        item_label = getattr(item, 'label', '') or getattr(item, 'name', '')
        if item_label not in hidden_labels:
            new_menu_items.append(item)
    menu_items[:] = new_menu_items


@hooks.register('insert_global_admin_js')
def global_admin_js():
    """Add JavaScript for employee assignment editing"""
    from django.urls import reverse
    from django.utils.html import format_html
    
    update_url = reverse('update_routine_service_employee')
    employees_url = reverse('get_employees_list')
    
    return format_html(
        '''
        <style>
        .employee-edit-container {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            background: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            min-width: 280px;
            position: relative;
            z-index: 1000;
        }}
        .employee-edit-select {{
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
            min-width: 200px;
            max-width: 250px;
            background: white;
            color: #374151;
            cursor: pointer;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        .employee-edit-select:hover {{
            border-color: #9ca3af;
        }}
        .employee-edit-select:focus {{
            outline: none;
            border-color: #007cba;
            box-shadow: 0 0 0 3px rgba(0, 124, 186, 0.1);
        }}
        .employee-edit-btn-container {{
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }}
        .employee-edit-btn-save {{
            padding: 8px 18px;
            background: #007cba;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .employee-edit-btn-save:hover {{
            background: #005a87;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 124, 186, 0.2);
        }}
        .employee-edit-btn-save:active {{
            transform: translateY(0);
        }}
        .employee-edit-btn-cancel {{
            padding: 8px 18px;
            background: #f9fafb;
            color: #374151;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .employee-edit-btn-cancel:hover {{
            background: #f3f4f6;
            border-color: #9ca3af;
            transform: translateY(-1px);
        }}
        .employee-edit-btn-cancel:active {{
            transform: translateY(0);
        }}
        .employee-edit-btn {{
            background: none !important;
            border: none !important;
            cursor: pointer;
            padding: 4px 8px !important;
            margin-left: 6px;
            opacity: 0.6;
            transition: opacity 0.2s, transform 0.2s;
            font-size: 16px;
            line-height: 1;
        }}
        .employee-edit-btn:hover {{
            opacity: 1;
            transform: scale(1.1);
        }}
        .employee-display {{
            display: inline-flex;
            align-items: center;
            position: relative;
        }}
        .download-pdf-link {{
            display: inline-flex !important;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            color: #007cba !important;
            text-decoration: none !important;
            border-radius: 4px;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}
        .download-pdf-link:hover {{
            background: #f0f9ff;
            border-color: #007cba;
        }}
        .download-pdf-link .icon {{
            width: 16px;
            height: 16px;
            fill: currentColor;
        }}
        .download-pdf-link:active {{
            transform: scale(0.95);
        }}
        </style>
        <script>
        function editEmployee(button, serviceId, serviceType) {{
            const span = button.closest('.employee-display');
            const actualServiceId = span.getAttribute('data-amc-service-id') || serviceId;
            
            // Show loading state
            const originalContent = span.innerHTML;
            span.innerHTML = '<span style="color: #6b7280;">Loading...</span>';
            
            fetch('{}')
                .then(response => response.json())
                .then(data => {{
                    if (!data.success) {{
                        span.innerHTML = originalContent;
                        alert('Error loading employees: ' + data.error);
                        return;
                    }}
                    
                    const employees = data.employees;
                    let optionsHtml = '<option value="">— Unassign —</option>';
                    employees.forEach(emp => {{
                        optionsHtml += `<option value="${{emp.id}}">${{emp.name}}</option>`;
                    }});
                    
                    const currentText = span.textContent.trim().replace('✏️', '').trim();
                    const currentEmployee = employees.find(e => e.name === currentText);
                    const selectedValue = currentEmployee ? currentEmployee.id : '';
                    
                    // Create container
                    const container = document.createElement('div');
                    container.className = 'employee-edit-container';
                    
                    // Create select dropdown
                    const select = document.createElement('select');
                    select.className = 'employee-edit-select';
                    select.innerHTML = optionsHtml;
                    select.value = selectedValue;
                    
                    // Create button container
                    const btnContainer = document.createElement('div');
                    btnContainer.className = 'employee-edit-btn-container';
                    
                    // Create save button
                    const saveBtn = document.createElement('button');
                    saveBtn.className = 'employee-edit-btn-save';
                    saveBtn.textContent = 'Save';
                    saveBtn.onclick = function(e) {{
                        e.stopPropagation();
                        saveEmployee(actualServiceId, select.value, serviceType, span, serviceId);
                    }};
                    
                    // Create cancel button
                    const cancelBtn = document.createElement('button');
                    cancelBtn.className = 'employee-edit-btn-cancel';
                    cancelBtn.textContent = 'Cancel';
                    cancelBtn.onclick = function(e) {{
                        e.stopPropagation();
                        span.innerHTML = originalContent;
                    }};
                    
                    btnContainer.appendChild(saveBtn);
                    btnContainer.appendChild(cancelBtn);
                    
                    container.appendChild(select);
                    container.appendChild(btnContainer);
                    
                    // Replace span content
                    span.innerHTML = '';
                    span.appendChild(container);
                    
                    // Focus on select
                    setTimeout(() => select.focus(), 100);
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    span.innerHTML = originalContent;
                    alert('Error loading employees');
                }});
        }}
        
        function saveEmployee(serviceId, employeeId, serviceType, parentElement, originalServiceId) {{
            const url = '{}';
            const data = {{
                service_id: serviceId,
                employee_id: employeeId || null,
                service_type: serviceType
            }};
            
            // Show saving state
            const container = parentElement.querySelector('.employee-edit-container');
            if (container) {{
                container.style.opacity = '0.6';
                container.style.pointerEvents = 'none';
            }}
            
            fetch(url, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    const employeeName = data.employee_name || '—';
                    const serviceIdAttr = parentElement.getAttribute('data-service-id');
                    const serviceTypeAttr = parentElement.getAttribute('data-service-type');
                    const amcServiceIdAttr = parentElement.getAttribute('data-amc-service-id') || '';
                    
                    parentElement.innerHTML = employeeName + ' <button class="employee-edit-btn" onclick="editEmployee(this, ' + serviceIdAttr + ', \\'' + serviceTypeAttr + '\\')" title="Edit Employee">✏️</button>';
                    parentElement.setAttribute('data-service-id', serviceIdAttr);
                    parentElement.setAttribute('data-service-type', serviceTypeAttr);
                    if (amcServiceIdAttr) {{
                        parentElement.setAttribute('data-amc-service-id', amcServiceIdAttr);
                    }}
                }} else {{
                    if (container) {{
                        container.style.opacity = '1';
                        container.style.pointerEvents = 'auto';
                    }}
                    alert('Error updating employee: ' + data.error);
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                if (container) {{
                    container.style.opacity = '1';
                    container.style.pointerEvents = 'auto';
                }}
                alert('Error updating employee');
            }});
        }}
        
        function getCookie(name) {{
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {{
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {{
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }}
                }}
            }}
            return cookieValue;
        }}
        </script>
        ''',
        employees_url,
        update_url
    )


@hooks.register('register_admin_urls')
def register_routine_service_urls():
    """Register API endpoints for routine services"""
    return [
        path('api/routine-services/update-employee/', update_routine_service_employee, name='update_routine_service_employee'),
        path('api/routine-services/get-employees/', get_employees_list, name='get_employees_list'),
    ]


@csrf_exempt
@require_http_methods(["GET"])
def get_employees_list(request):
    """API endpoint to get list of employees"""
    try:
        User = get_user_model()
        employees = User.objects.filter(is_active=True).order_by('username')
        employees_list = []
        for emp in employees:
            employees_list.append({
                'id': emp.id,
                'name': emp.get_full_name() if emp.get_full_name() else emp.username,
                'username': emp.username
            })
        return JsonResponse({
            'success': True,
            'employees': employees_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_routine_service_employee(request):
    """API endpoint to update employee assignment for routine services"""
    try:
        data = json.loads(request.body)
        service_id = data.get('service_id')
        employee_id = data.get('employee_id')
        service_type = data.get('service_type', 'regular')  # 'regular' or 'amc'
        
        if not service_id:
            return JsonResponse({
                'success': False,
                'error': 'Service ID is required'
            }, status=400)
        
        User = get_user_model()
        
        if service_type == 'amc':
            # Handle AMC routine service
            # service_id might be in format "amc_123" or just the ID
            if isinstance(service_id, str) and service_id.startswith('amc_'):
                actual_id = service_id.replace('amc_', '')
            else:
                actual_id = service_id
            
            try:
                actual_id = int(actual_id)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid service ID format'
                }, status=400)
            
            service = get_object_or_404(AMCRoutineService, pk=actual_id)
            if employee_id:
                employee = get_object_or_404(User, pk=employee_id)
                service.employee_assign = employee
            else:
                service.employee_assign = None
            service.save()
            
            employee_name = service.employee_assign.get_full_name() if service.employee_assign else "Unassigned"
            if not employee_name and service.employee_assign:
                employee_name = service.employee_assign.username
        else:
            # Handle regular routine service
            try:
                service_id = int(service_id)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid service ID format'
                }, status=400)
            
            service = get_object_or_404(RoutineService, pk=service_id)
            if employee_id:
                employee = get_object_or_404(User, pk=employee_id)
                service.assigned_technician = employee
            else:
                service.assigned_technician = None
            service.save()
            
            employee_name = service.assigned_technician.get_full_name() if service.assigned_technician else "Unassigned"
            if not employee_name and service.assigned_technician:
                employee_name = service.assigned_technician.username
        
        return JsonResponse({
            'success': True,
            'employee_name': employee_name,
            'message': 'Employee assignment updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)