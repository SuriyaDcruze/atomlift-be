from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Complaint, ComplaintType, ComplaintPriority, ComplaintAssignmentHistory, ComplaintStatusHistory
from customer.models import Customer

User = get_user_model()


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    class Meta:
        model = Customer
        fields = [
            'id', 'reference_id', 'site_id', 'job_no', 'site_name', 
            'site_address', 'email', 'phone', 'mobile', 'contact_person_name',
            'designation', 'city', 'branch', 'routes'
        ]


class ComplaintTypeSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintType model"""
    class Meta:
        model = ComplaintType
        fields = ['id', 'name']


class ComplaintPrioritySerializer(serializers.ModelSerializer):
    """Serializer for ComplaintPriority model"""
    class Meta:
        model = ComplaintPriority
        fields = ['id', 'name']


class ComplaintAssignmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for ComplaintAssignmentHistory model"""
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintAssignmentHistory
        fields = [
            'id', 'assigned_to_name', 'assigned_by_name', 
            'assignment_date', 'subject', 'message', 'created'
        ]
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.email
        return None
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip() or obj.assigned_by.email
        return None


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for ComplaintStatusHistory model"""
    changed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintStatusHistory
        fields = [
            'id', 'old_status', 'new_status', 'changed_by_name',
            'change_reason', 'technician_remark', 'solution',
            'changed_at', 'changed_from_mobile'
        ]
    
    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return f"{obj.changed_by.first_name} {obj.changed_by.last_name}".strip() or obj.changed_by.email
        return None


class ComplaintListSerializer(serializers.ModelSerializer):
    """Serializer for complaint list view (mobile app)"""
    customer = CustomerSerializer(read_only=True)
    complaint_type = ComplaintTypeSerializer(read_only=True)
    priority = ComplaintPrioritySerializer(read_only=True)
    assign_to_name = serializers.SerializerMethodField()
    days_since_created = serializers.SerializerMethodField()
    technician_signature = serializers.ImageField(read_only=True)
    customer_signature = serializers.ImageField(read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'reference', 'complaint_type', 'date', 'customer',
            'contact_person_name', 'contact_person_mobile', 'block_wing',
            'status', 'lift_info', 'complaint_templates', 'assign_to_name',
            'priority', 'subject', 'message', 'technician_remark', 'solution',
            'technician_signature', 'customer_signature',
            'created', 'updated', 'days_since_created'
        ]
    
    def get_assign_to_name(self, obj):
        if obj.assign_to:
            return f"{obj.assign_to.first_name} {obj.assign_to.last_name}".strip() or obj.assign_to.email
        return None
    
    def get_days_since_created(self, obj):
        from django.utils import timezone
        delta = timezone.now().date() - obj.date
        return delta.days


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed complaint view (mobile app)"""
    customer = CustomerSerializer(read_only=True)
    complaint_type = ComplaintTypeSerializer(read_only=True)
    priority = ComplaintPrioritySerializer(read_only=True)
    assign_to_name = serializers.SerializerMethodField()
    assignment_history = ComplaintAssignmentHistorySerializer(many=True, read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    days_since_created = serializers.SerializerMethodField()
    technician_signature = serializers.CharField(read_only=True)
    customer_signature = serializers.CharField(read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'reference', 'complaint_type', 'date', 'customer',
            'contact_person_name', 'contact_person_mobile', 'block_wing',
            'status', 'lift_info', 'complaint_templates', 'assign_to_name',
            'priority', 'subject', 'message', 'technician_remark', 'solution',
            'technician_signature', 'customer_signature',
            'created', 'updated', 'days_since_created', 'assignment_history', 'status_history'
        ]
    
    def get_assign_to_name(self, obj):
        if obj.assign_to:
            return f"{obj.assign_to.first_name} {obj.assign_to.last_name}".strip() or obj.assign_to.email
        return None
    
    def get_days_since_created(self, obj):
        from django.utils import timezone
        delta = timezone.now().date() - obj.date
        return delta.days


class ComplaintUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating complaint status and remarks"""
    change_reason = serializers.CharField(required=False, allow_blank=True, help_text="Reason for status change")
    
    technician_signature = serializers.ImageField(required=False, allow_null=True)
    customer_signature = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Complaint
        fields = ['status', 'technician_remark', 'solution', 'technician_signature', 'customer_signature', 'change_reason']
    
    def validate_status(self, value):
        """Validate status transition"""
        valid_statuses = ['open', 'in_progress', 'closed']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating complaint from mobile app"""
    
    class Meta:
        model = Complaint
        fields = [
            'customer', 'complaint_type', 'date', 'priority', 'status',
            'contact_person_name', 'contact_person_mobile', 'block_wing',
            'lift_info', 'complaint_templates', 'subject', 'message', 'assign_to'
        ]
    
    def validate_customer(self, value):
        """Ensure customer exists"""
        if not value:
            raise serializers.ValidationError("Customer is required")
        return value
    
    def validate_subject(self, value):
        """Ensure subject is provided"""
        if not value or not value.strip():
            raise serializers.ValidationError("Subject is required")
        return value.strip()
    
    def validate_message(self, value):
        """Ensure message is provided"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message is required")
        return value.strip()
    
    def validate_status(self, value):
        """Validate status"""
        valid_statuses = ['open', 'in_progress', 'closed']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def create(self, validated_data):
        """Create complaint and automatically assign to the logged-in employee"""
        # assign_to is already set in validated_data by the view
        # Create the complaint (assign_to is included in validated_data)
        complaint = Complaint.objects.create(**validated_data)
        return complaint


class ComplaintEditSerializer(serializers.ModelSerializer):
    """Serializer for editing all complaint fields from mobile app"""
    
    class Meta:
        model = Complaint
        fields = [
            'customer', 'complaint_type', 'date', 'priority', 'status',
            'contact_person_name', 'contact_person_mobile', 'block_wing',
            'lift_info', 'complaint_templates', 'subject', 'message',
            'technician_remark', 'solution'
        ]
    
    def validate_subject(self, value):
        """Ensure subject is provided if being updated"""
        if value and not value.strip():
            raise serializers.ValidationError("Subject cannot be empty")
        return value.strip() if value else value
    
    def validate_message(self, value):
        """Ensure message is provided if being updated"""
        if value and not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip() if value else value
    
    def validate_status(self, value):
        """Validate status"""
        if value:
            valid_statuses = ['open', 'in_progress', 'closed']
            if value not in valid_statuses:
                raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def update(self, instance, validated_data):
        """Update complaint fields"""
        # Update all provided fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance