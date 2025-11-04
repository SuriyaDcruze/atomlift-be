from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime
from .models import AttendanceRecord
from .serializers import (
    AttendanceRecordSerializer,
    CheckInSerializer,
    WorkCheckInSerializer,
    CheckOutSerializer
)
import logging

logger = logging.getLogger(__name__)


class AttendancePagination(PageNumberPagination):
    """Custom pagination for attendance records"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_attendance_in(request):
    """
    Step 1: Mark attendance in with selfie (Mobile app).
    Creates a new attendance record with check-in details.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can mark attendance."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CheckInSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            today = date.today()
            now = timezone.now()
            
            # Check if record already exists for today
            attendance_record, created = AttendanceRecord.objects.get_or_create(
                user=user,
                check_in_date=today,
                defaults={
                    'check_in_time': now,
                    'is_checked_in': True,
                }
            )
            
            # If record exists but not checked in, update it
            if not created and not attendance_record.is_checked_in:
                attendance_record.check_in_time = now
                attendance_record.is_checked_in = True
            
            # Update check-in details
            if 'selfie' in request.FILES:
                attendance_record.check_in_selfie = request.FILES['selfie']
            if serializer.validated_data.get('location'):
                attendance_record.check_in_location = serializer.validated_data['location']
            if serializer.validated_data.get('note'):
                attendance_record.check_in_note = serializer.validated_data['note']
            
            attendance_record.save()
            
            # Return attendance record
            response_serializer = AttendanceRecordSerializer(attendance_record)
            return Response(
                {
                    "message": "Attendance marked successfully",
                    "attendance": response_serializer.data
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error marking attendance in: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def work_check_in(request):
    """
    Step 2: Work check-in with note (Mobile app).
    Updates the existing attendance record with work check-in note.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can mark work check-in."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = WorkCheckInSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            today = date.today()
            
            # Get existing attendance record
            attendance_record = AttendanceRecord.objects.filter(
                user=user,
                check_in_date=today
            ).first()
            
            if not attendance_record:
                return Response(
                    {"error": "Please complete step 1 (Mark Attendance In) first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update check-in note if provided
            if serializer.validated_data.get('note'):
                attendance_record.check_in_note = serializer.validated_data['note']
                attendance_record.save()
            
            # Return updated attendance record
            response_serializer = AttendanceRecordSerializer(attendance_record)
            return Response(
                {
                    "message": "Work check-in completed successfully",
                    "attendance": response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in work check-in: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_out(request):
    """
    Check out from work (Mobile app).
    Updates the attendance record with check-out details.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can check out."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CheckOutSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            today = date.today()
            now = timezone.now()
            
            # Get existing attendance record
            attendance_record = AttendanceRecord.objects.filter(
                user=user,
                check_in_date=today,
                is_checked_in=True
            ).first()
            
            if not attendance_record:
                return Response(
                    {"error": "You must check in before checking out."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if attendance_record.is_checked_out:
                return Response(
                    {"error": "You have already checked out today."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update check-out details
            attendance_record.check_out_time = now
            attendance_record.check_out_date = today
            attendance_record.is_checked_out = True
            
            if serializer.validated_data.get('location'):
                attendance_record.check_out_location = serializer.validated_data['location']
            if serializer.validated_data.get('note'):
                attendance_record.check_out_note = serializer.validated_data['note']
            
            attendance_record.save()
            
            # Return updated attendance record
            response_serializer = AttendanceRecordSerializer(attendance_record)
            return Response(
                {
                    "message": "Check-out completed successfully",
                    "attendance": response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error checking out: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_attendance(request):
    """
    Get attendance records for the authenticated user (Mobile app).
    Returns paginated list of attendance records.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can view attendance."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all attendance records for this user
        queryset = AttendanceRecord.objects.filter(user=request.user).order_by('-check_in_date', '-check_in_time')
        
        # Apply filters
        date_filter = request.query_params.get('date')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        search = request.query_params.get('q', '')
        
        if date_filter:
            queryset = queryset.filter(check_in_date=date_filter)
        
        if start_date:
            queryset = queryset.filter(check_in_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(check_in_date__lte=end_date)
        
        if search:
            queryset = queryset.filter(
                Q(check_in_location__icontains=search) |
                Q(check_in_note__icontains=search) |
                Q(check_out_location__icontains=search) |
                Q(check_out_note__icontains=search)
            )
        
        # Paginate results
        paginator = AttendancePagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AttendanceRecordSerializer(page, many=True)
            return paginator.get_paginated_response({
                "attendance_records": serializer.data
            })
        
        # If no pagination
        serializer = AttendanceRecordSerializer(queryset, many=True)
        return Response(
            {
                "count": queryset.count(),
                "attendance_records": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error getting user attendance: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_attendance(request):
    """
    Get today's attendance record for the authenticated user (Mobile app).
    Returns current day's attendance status.
    """
    try:
        # Check if user is in any employee group
        if not request.user.groups.exists():
            return Response(
                {"error": "Access denied. Only employees can view attendance."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        today = date.today()
        attendance_record = AttendanceRecord.objects.filter(
            user=request.user,
            check_in_date=today
        ).first()
        
        if attendance_record:
            serializer = AttendanceRecordSerializer(attendance_record)
            return Response(
                {
                    "attendance": serializer.data,
                    "has_checked_in": attendance_record.is_checked_in,
                    "has_checked_out": attendance_record.is_checked_out
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "attendance": None,
                    "has_checked_in": False,
                    "has_checked_out": False,
                    "message": "No attendance record for today"
                },
                status=status.HTTP_200_OK
            )
    
    except Exception as e:
        logger.error(f"Error getting today's attendance: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance_detail(request, pk):
    """
    Get details of a specific attendance record.
    Users can only view their own attendance records.
    Admins can view any attendance record.
    """
    try:
        attendance_record = get_object_or_404(AttendanceRecord, pk=pk)
        
        # Check permissions
        if not request.user.groups.exists() and not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Access denied. Only employees and admins can view attendance records."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Users can only view their own records, admins can view all
        if not (request.user.is_staff or request.user.is_superuser):
            if attendance_record.user != request.user:
                return Response(
                    {"error": "Access denied. You can only view your own attendance records."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = AttendanceRecordSerializer(attendance_record)
        return Response(
            {"attendance": serializer.data},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error getting attendance detail: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_attendance(request):
    """
    List all attendance records (Admin only).
    Admin can view all attendance records from all users.
    Requires admin/staff permissions.
    """
    try:
        # Check if user is admin/staff
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Access denied. Only admins can view all attendance records."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all attendance records
        queryset = AttendanceRecord.objects.all().order_by('-check_in_date', '-check_in_time')
        
        # Apply filters
        user_id = request.query_params.get('user_id')
        date_filter = request.query_params.get('date')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        search = request.query_params.get('q', '')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if date_filter:
            queryset = queryset.filter(check_in_date=date_filter)
        
        if start_date:
            queryset = queryset.filter(check_in_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(check_in_date__lte=end_date)
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(check_in_location__icontains=search) |
                Q(check_in_note__icontains=search) |
                Q(check_out_location__icontains=search) |
                Q(check_out_note__icontains=search)
            )
        
        # Paginate results
        paginator = AttendancePagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AttendanceRecordSerializer(page, many=True)
            return paginator.get_paginated_response({
                "attendance_records": serializer.data
            })
        
        # If no pagination
        serializer = AttendanceRecordSerializer(queryset, many=True)
        return Response(
            {
                "count": queryset.count(),
                "attendance_records": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error listing all attendance: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
