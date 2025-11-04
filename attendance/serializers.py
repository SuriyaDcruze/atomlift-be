from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AttendanceRecord
from django.utils import timezone
from datetime import date

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User information in attendance records"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRecord model"""
    user_detail = UserSerializer(source='user', read_only=True)
    work_duration = serializers.SerializerMethodField()
    work_duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'user', 'user_detail',
            'check_in_time', 'check_in_date', 'check_in_selfie', 
            'check_in_location', 'check_in_note',
            'check_out_time', 'check_out_date', 
            'check_out_location', 'check_out_note',
            'is_checked_in', 'is_checked_out',
            'work_duration', 'work_duration_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'check_in_time', 'check_in_date',
            'check_out_time', 'check_out_date',
            'is_checked_in', 'is_checked_out',
            'created_at', 'updated_at'
        ]
    
    def get_work_duration(self, obj):
        """Get work duration in hours"""
        return obj.calculate_work_duration()
    
    def get_work_duration_display(self, obj):
        """Get work duration as formatted string"""
        return obj.get_work_duration_display()


class CheckInSerializer(serializers.Serializer):
    """Serializer for check-in action"""
    selfie = serializers.ImageField(required=False, allow_null=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate check-in data"""
        # Check if user already checked in today
        user = self.context['request'].user
        today = date.today()
        
        existing_record = AttendanceRecord.objects.filter(
            user=user,
            check_in_date=today,
            is_checked_in=True
        ).first()
        
        if existing_record and not existing_record.is_checked_out:
            raise serializers.ValidationError({
                'error': 'You have already checked in today. Please check out first.'
            })
        
        return data


class WorkCheckInSerializer(serializers.Serializer):
    """Serializer for work check-in (step 2) with note"""
    note = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate work check-in data"""
        user = self.context['request'].user
        today = date.today()
        
        # Check if user has a check-in record for today
        existing_record = AttendanceRecord.objects.filter(
            user=user,
            check_in_date=today
        ).first()
        
        if not existing_record:
            raise serializers.ValidationError({
                'error': 'Please complete step 1 (Mark Attendance In) first.'
            })
        
        if existing_record.check_in_note:
            raise serializers.ValidationError({
                'error': 'Work check-in note already submitted for today.'
            })
        
        return data


class CheckOutSerializer(serializers.Serializer):
    """Serializer for check-out action"""
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate check-out data"""
        user = self.context['request'].user
        today = date.today()
        
        # Check if user has checked in today
        existing_record = AttendanceRecord.objects.filter(
            user=user,
            check_in_date=today,
            is_checked_in=True
        ).first()
        
        if not existing_record:
            raise serializers.ValidationError({
                'error': 'You must check in before checking out.'
            })
        
        if existing_record.is_checked_out:
            raise serializers.ValidationError({
                'error': 'You have already checked out today.'
            })
        
        return data

