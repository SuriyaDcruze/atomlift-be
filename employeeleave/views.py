from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import format_html
import logging
from .models import LeaveRequest
from .serializers import (
    LeaveRequestSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestUserUpdateSerializer,
    LeaveRequestUpdateSerializer
)

logger = logging.getLogger(__name__)


def get_user_leave_counts(user):
    """
    Calculate leave counts for a specific user
    Returns: dict with total, pending, approved, rejected counts
    """
    from .models import LeaveRequest
    
    counts = LeaveRequest.objects.filter(user=user).aggregate(
        total=models.Count('id'),
        pending=models.Count('id', filter=models.Q(status='pending')),
        approved=models.Count('id', filter=models.Q(status='approved')),
        rejected=models.Count('id', filter=models.Q(status='rejected')),
    )
    
    return {
        'total': counts['total'] or 0,
        'pending': counts['pending'] or 0,
        'approved': counts['approved'] or 0,
        'rejected': counts['rejected'] or 0,
    }


class LeaveRequestPagination(PageNumberPagination):
    """Custom pagination for leave requests"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def send_leave_status_email(leave_request, old_status, new_status):
    """
    Send email notification to user when leave request status changes
    """
    try:
        user = leave_request.user
        user_email = leave_request.email or user.email
        
        if not user_email:
            logger.warning(f"No email found for user {user.id}, cannot send leave status email")
            return False
        
        # Prepare email content based on status
        if new_status == 'approved':
            subject = 'Leave Request Approved'
            status_message = 'approved'
            status_color = '#4caf50'
        elif new_status == 'rejected':
            subject = 'Leave Request Rejected'
            status_message = 'rejected'
            status_color = '#f44336'
        else:
            # Don't send email for pending status
            return False
        
        # Format dates
        from_date_str = leave_request.from_date.strftime("%B %d, %Y")
        to_date_str = leave_request.to_date.strftime("%B %d, %Y")
        if leave_request.from_date == leave_request.to_date:
            date_range = from_date_str
        else:
            date_range = f"{from_date_str} to {to_date_str}"
        
        # Prepare email message
        message = f"""
Dear {user.get_full_name() or user.email},

Your leave request has been {status_message.upper()}.

Leave Details:
• Leave Type: {leave_request.get_leave_type_display()}
• Date(s): {date_range}
• Half Day: {'Yes' if leave_request.half_day else 'No'}
"""
        
        if leave_request.reason:
            message += f"• Reason: {leave_request.reason}\n"
        
        if leave_request.admin_remarks:
            message += f"\nAdmin Remarks:\n{leave_request.admin_remarks}\n"
        
        message += f"""
Thank you for using the Leave Management System.

Best regards,
Leave Management Team
"""
        
        # Send email
        from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@example.com')
        recipient_list = [user_email]
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        logger.info(f"Leave status email sent to {user_email} for leave request {leave_request.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send leave status email: {e}", exc_info=True)
        return False


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_leave_request(request):
    """
    Create a new leave request from mobile app.
    Requires authentication token.
    User can create leave request for themselves.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can create leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create serializer with user automatically set
        serializer = LeaveRequestCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create leave request with the authenticated user
            leave_request = serializer.save(user=request.user)
            
            # Return full details
            response_serializer = LeaveRequestSerializer(leave_request)
            return Response(
                {
                    "message": "Leave request created successfully",
                    "leave_request": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_leave_requests(request):
    """
    List all leave requests for the authenticated user (mobile app).
    Requires authentication token.
    Returns only leave requests created by the logged-in user.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can view leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all leave requests for this user
        queryset = LeaveRequest.objects.filter(user=request.user).order_by('-created_at')

        # Apply filters
        status_filter = request.query_params.get('status')
        leave_type_filter = request.query_params.get('leave_type')
        search = request.query_params.get('q', '')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if leave_type_filter:
            queryset = queryset.filter(leave_type=leave_type_filter)
        
        if search:
            queryset = queryset.filter(
                Q(leave_type__icontains=search) |
                Q(reason__icontains=search) |
                Q(status__icontains=search)
            )

        # Get leave counts for the user
        leave_counts = get_user_leave_counts(request.user)

        # Paginate results
        paginator = LeaveRequestPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LeaveRequestSerializer(page, many=True)
            paginated_response = paginator.get_paginated_response({
                "leave_requests": serializer.data
            })
            # Add leave counts to paginated response
            paginated_response.data['leave_counts'] = leave_counts
            return paginated_response

        # If no pagination
        serializer = LeaveRequestSerializer(queryset, many=True)
        return Response(
            {
                "count": queryset.count(),
                "leave_requests": serializer.data,
                "leave_counts": leave_counts
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leave_request_detail(request, pk):
    """
    Get details of a specific leave request.
    Users can only view their own leave requests.
    Admins can view any leave request.
    """
    try:
        leave_request = get_object_or_404(LeaveRequest, pk=pk)

        # Check permissions
        if not request.user.groups.exists() and not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Access denied. Only employees and admins can view leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Users can only view their own requests, admins can view all
        if not (request.user.is_staff or request.user.is_superuser):
            if leave_request.user != request.user:
                return Response(
                    {"error": "Access denied. You can only view your own leave requests."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = LeaveRequestSerializer(leave_request)
        return Response(
            {"leave_request": serializer.data},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_user_leave_request(request, pk):
    """
    Update user's own leave request (Mobile app).
    Users can only update their own leave requests.
    Users can only update leave requests with 'pending' status.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can update leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = get_object_or_404(LeaveRequest, pk=pk)

        # Check if user owns this leave request
        if leave_request.user != request.user:
            return Response(
                {"error": "Access denied. You can only update your own leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only allow updating pending leave requests
        if leave_request.status != 'pending':
            return Response(
                {
                    "error": f"Cannot update leave request. Current status is '{leave_request.status}'. Only pending leave requests can be updated."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaveRequestUserUpdateSerializer(
            leave_request,
            data=request.data,
            partial=True  # Allow partial updates for PATCH
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Return updated leave request with full details
            response_serializer = LeaveRequestSerializer(leave_request)
            return Response(
                {
                    "message": "Leave request updated successfully",
                    "leave_request": response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_leave_request(request, pk):
    """
    Delete user's own leave request (Mobile app).
    Users can only delete their own leave requests.
    Users can only delete leave requests with 'pending' status.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can delete leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = get_object_or_404(LeaveRequest, pk=pk)

        # Check if user owns this leave request
        if leave_request.user != request.user:
            return Response(
                {"error": "Access denied. You can only delete your own leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only allow deleting pending leave requests
        if leave_request.status != 'pending':
            return Response(
                {
                    "error": f"Cannot delete leave request. Current status is '{leave_request.status}'. Only pending leave requests can be deleted."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store details for response
        leave_id = leave_request.id
        leave_type = leave_request.leave_type
        from_date = leave_request.from_date
        to_date = leave_request.to_date

        # Delete the leave request
        leave_request.delete()

        return Response(
            {
                "message": "Leave request deleted successfully",
                "deleted_leave_request": {
                    "id": leave_id,
                    "leave_type": leave_type,
                    "from_date": str(from_date),
                    "to_date": str(to_date)
                }
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_leave_requests(request):
    """
    List all leave requests (Admin only).
    Admin can view all leave requests from all users.
    Requires admin/staff permissions.
    """
    try:
        # Check if user is admin/staff
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Access denied. Only admins can view all leave requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all leave requests
        queryset = LeaveRequest.objects.all().order_by('-created_at')

        # Apply filters
        status_filter = request.query_params.get('status')
        leave_type_filter = request.query_params.get('leave_type')
        user_id = request.query_params.get('user_id')
        search = request.query_params.get('q', '')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if leave_type_filter:
            queryset = queryset.filter(leave_type=leave_type_filter)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(leave_type__icontains=search) |
                Q(reason__icontains=search) |
                Q(status__icontains=search)
            )

        # Paginate results
        paginator = LeaveRequestPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LeaveRequestSerializer(page, many=True)
            return paginator.get_paginated_response({
                "leave_requests": serializer.data
            })

        # If no pagination
        serializer = LeaveRequestSerializer(queryset, many=True)
        return Response(
            {
                "count": queryset.count(),
                "leave_requests": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_leave_request_status(request, pk):
    """
    Update leave request status (Approve/Reject) - Admin only.
    Admin can approve or reject leave requests and add remarks.
    Requires admin/staff permissions.
    """
    try:
        # Check if user is admin/staff
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Access denied. Only admins can update leave request status."},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = get_object_or_404(LeaveRequest, pk=pk)

        # Only allow updating status from pending
        if leave_request.status != 'pending' and request.data.get('status') != leave_request.status:
            return Response(
                {
                    "error": f"Cannot change status. Current status is '{leave_request.status}'. Only pending requests can be updated."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaveRequestUpdateSerializer(
            leave_request,
            data=request.data,
            partial=True  # Allow partial updates for PATCH
        )
        
        if serializer.is_valid():
            # Store old status before saving
            old_status = leave_request.status
            new_status = serializer.validated_data.get('status', leave_request.status)
            
            serializer.save()
            
            # Reload to get updated instance
            leave_request.refresh_from_db()
            
            # Send email notification if status changed to approved or rejected
            if old_status != new_status and new_status in ['approved', 'rejected']:
                try:
                    send_leave_status_email(leave_request, old_status, new_status)
                except Exception as e:
                    logger.error(f"Error sending leave status email: {e}")
                    # Don't fail the request if email fails
            
            # Return updated leave request with full details
            response_serializer = LeaveRequestSerializer(leave_request)
            return Response(
                {
                    "message": "Leave request status updated successfully",
                    "leave_request": response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leave_types(request):
    """
    Return all available leave types for the mobile app.
    """
    leave_types = [
        {"id": 1, "key": "casual", "name": "Casual Leave"},
        {"id": 2, "key": "sick", "name": "Sick Leave"},
        {"id": 3, "key": "earned", "name": "Earned Leave"},
        {"id": 4, "key": "unpaid", "name": "Unpaid Leave"},
        {"id": 5, "key": "other", "name": "Other"},
    ]
    return Response(leave_types)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_leave_counts_api(request):
    """
    Get leave counts for the authenticated user (Mobile app).
    Returns total, pending, approved, and rejected counts.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can view leave counts."},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_counts = get_user_leave_counts(request.user)
        
        return Response(
            {
                "leave_counts": leave_counts,
                "user": {
                    "id": request.user.id,
                    "email": request.user.email,
                    "full_name": request.user.get_full_name()
                }
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
