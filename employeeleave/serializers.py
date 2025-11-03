from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LeaveRequest

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User information in leave requests"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest model"""
    user_detail = UserSerializer(source='user', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'user', 'user_detail', 'half_day', 'leave_type', 
            'leave_type_display', 'from_date', 'to_date', 'reason', 
            'email', 'status', 'status_display', 'admin_remarks', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'admin_remarks', 'created_at', 'updated_at']


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave requests"""
    
    class Meta:
        model = LeaveRequest
        fields = [
            'half_day', 'leave_type', 'from_date', 'to_date', 
            'reason', 'email'
        ]
    
    def validate(self, data):
        """Validate that to_date is after from_date"""
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError({
                'to_date': 'To date must be after or equal to from date.'
            })
        
        return data


class LeaveRequestUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for users to update their own leave requests"""
    
    class Meta:
        model = LeaveRequest
        fields = [
            'half_day', 'leave_type', 'from_date', 'to_date', 
            'reason', 'email'
        ]
    
    def validate(self, data):
        """Validate that to_date is after from_date"""
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError({
                'to_date': 'To date must be after or equal to from date.'
            })
        
        return data


class LeaveRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to update leave request status"""
    
    class Meta:
        model = LeaveRequest
        fields = ['status', 'admin_remarks']
    
    def validate_status(self, value):
        """Validate status values"""
        valid_statuses = ['pending', 'approved', 'rejected']
        if value not in valid_statuses:
            raise serializers.ValidationError(f'Status must be one of: {", ".join(valid_statuses)}')
        return value

