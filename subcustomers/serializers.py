from rest_framework import serializers
from .models import SubCustomer
from customer.models import Customer


class SubCustomerSerializer(serializers.ModelSerializer):
    """Serializer for SubCustomer with customer details"""
    customer_id = serializers.IntegerField(source='customer.id', read_only=True)
    customer_name = serializers.CharField(source='customer.site_name', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    
    class Meta:
        model = SubCustomer
        fields = [
            'id', 'customer_id', 'customer_name', 'customer_email',
            'name', 'email', 'phone', 'can_access_app', 'is_active',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubCustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new sub-customer"""
    
    class Meta:
        model = SubCustomer
        fields = ['name', 'email', 'phone', 'can_access_app']
    
    def validate_email(self, value):
        """Validate email is provided"""
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value
    
    def validate_name(self, value):
        """Validate name is provided"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()


class SubCustomerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a sub-customer"""
    
    class Meta:
        model = SubCustomer
        fields = ['name', 'email', 'phone', 'can_access_app', 'is_active']
    
    def validate_name(self, value):
        """Validate name is provided"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value.strip() if value else value


class SubCustomerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing sub-customers"""
    customer_name = serializers.CharField(source='customer.site_name', read_only=True)
    
    class Meta:
        model = SubCustomer
        fields = [
            'id', 'customer_name', 'name', 'email', 'phone', 
            'can_access_app', 'is_active', 'created_at'
        ]



