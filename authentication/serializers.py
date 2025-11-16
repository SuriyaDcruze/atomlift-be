from rest_framework import serializers
from django.contrib.auth import get_user_model
import re
from .models import CustomUser, UserProfile, OTP

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'branch', 'route', 'code', 'designation']
    
    def validate_phone_number(self, value):
        """Validate mobile number - must be exactly 10 digits"""
        if value:
            # Remove any spaces, dashes, or other characters
            phone_number = re.sub(r'[\s\-\(\)]', '', value.strip())
            # Check if it contains only digits
            if not phone_number.isdigit():
                raise serializers.ValidationError('Mobile number must contain only digits.')
            # Check if it's exactly 10 digits
            if len(phone_number) != 10:
                raise serializers.ValidationError('Mobile number must be exactly 10 digits.')
            return phone_number
        return value


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number', 
                 'is_active', 'date_joined', 'last_login', 'profile', 'groups']
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def validate_phone_number(self, value):
        """Validate mobile number - must be exactly 10 digits"""
        if value:
            # Remove any spaces, dashes, or other characters
            phone_number = re.sub(r'[\s\-\(\)]', '', value.strip())
            # Check if it contains only digits
            if not phone_number.isdigit():
                raise serializers.ValidationError('Mobile number must contain only digits.')
            # Check if it's exactly 10 digits
            if len(phone_number) != 10:
                raise serializers.ValidationError('Mobile number must be exactly 10 digits.')
            return phone_number
        return value
    
    def get_full_name(self, obj):
        """Return the user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['otp_code', 'otp_type', 'contact_info', 'created_at', 'expires_at']
        read_only_fields = ['otp_code', 'created_at', 'expires_at']


class GenerateOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    
    def validate_phone_number(self, value):
        """Validate mobile number - must be exactly 10 digits"""
        if value:
            # Remove any spaces, dashes, or other characters
            phone_number = re.sub(r'[\s\-\(\)]', '', value.strip())
            # Check if it contains only digits
            if not phone_number.isdigit():
                raise serializers.ValidationError('Mobile number must contain only digits.')
            # Check if it's exactly 10 digits
            if len(phone_number) != 10:
                raise serializers.ValidationError('Mobile number must be exactly 10 digits.')
            return phone_number
        return value
    
    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')
        
        if not email and not phone_number:
            raise serializers.ValidationError("Either email or phone number is required")
        
        if email and phone_number:
            raise serializers.ValidationError("Provide either email or phone number, not both")
        
        return data


class VerifyOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_phone_number(self, value):
        """Validate mobile number - must be exactly 10 digits"""
        if value:
            # Remove any spaces, dashes, or other characters
            phone_number = re.sub(r'[\s\-\(\)]', '', value.strip())
            # Check if it contains only digits
            if not phone_number.isdigit():
                raise serializers.ValidationError('Mobile number must contain only digits.')
            # Check if it's exactly 10 digits
            if len(phone_number) != 10:
                raise serializers.ValidationError('Mobile number must be exactly 10 digits.')
            return phone_number
        return value
    
    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')
        
        if not email and not phone_number:
            raise serializers.ValidationError("Either email or phone number is required")
        
        if email and phone_number:
            raise serializers.ValidationError("Provide either email or phone number, not both")
        
        return data


class MobileLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    token = serializers.CharField()
    message = serializers.CharField()


class OTPSendResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    otp_type = serializers.CharField()
    contact_info = serializers.CharField()
    expires_in_minutes = serializers.IntegerField()


class EmailPasswordLoginRequestSerializer(serializers.Serializer):
    """
    Request serializer for mobile email + password login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)