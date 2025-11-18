from rest_framework import serializers
from .models import AMC, AMCType, PaymentTerms, AMCRoutineService
from customer.models import Customer
from items.models import Item


class AMCCreateSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), required=True
    )
    amc_type = serializers.PrimaryKeyRelatedField(
        queryset=AMCType.objects.all(), required=False, allow_null=True
    )
    payment_terms = serializers.PrimaryKeyRelatedField(
        queryset=PaymentTerms.objects.all(), required=False, allow_null=True
    )
    amc_service_item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = AMC
        fields = [
            'customer', 'latitude', 'equipment_no', 'invoice_frequency',
            'amc_type', 'payment_terms', 'start_date', 'end_date', 'notes',
            'is_generate_contract', 'no_of_services', 'price', 'no_of_lifts',
            'gst_percentage', 'amc_service_item'
        ]

    def validate(self, attrs):
        if not attrs.get('customer'):
            raise serializers.ValidationError({'customer': 'Customer is required.'})
        if not attrs.get('start_date'):
            raise serializers.ValidationError({'start_date': 'Start date is required.'})
        return attrs

    def create(self, validated_data):
        amc = AMC.objects.create(**validated_data)
        return amc


class AMCListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_site_address = serializers.SerializerMethodField()
    customer_job_no = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    amc_type_name = serializers.SerializerMethodField()
    payment_terms_name = serializers.SerializerMethodField()
    invoice_frequency_display = serializers.CharField(source='get_invoice_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AMC
        fields = [
            'id', 'reference_id', 'latitude', 'equipment_no',
            'invoice_frequency', 'invoice_frequency_display', 'start_date', 'end_date',
            'notes', 'is_generate_contract', 'no_of_services', 'price',
            'no_of_lifts', 'gst_percentage', 'total', 'contract_amount',
            'total_amount_paid', 'amount_due', 'status', 'status_display',
            'created', 'customer_name', 'customer_site_address', 'customer_job_no',
            'customer_email', 'customer_phone', 'amc_type_name', 'payment_terms_name'
        ]

    def get_customer_name(self, obj):
        return getattr(obj.customer, 'site_name', None)

    def get_customer_site_address(self, obj):
        return getattr(obj.customer, 'site_address', None)

    def get_customer_job_no(self, obj):
        return getattr(obj.customer, 'job_no', None)

    def get_customer_email(self, obj):
        return getattr(obj.customer, 'email', None)

    def get_customer_phone(self, obj):
        return getattr(obj.customer, 'phone', None)

    def get_amc_type_name(self, obj):
        return getattr(obj.amc_type, 'name', None)

    def get_payment_terms_name(self, obj):
        return getattr(obj.payment_terms, 'name', None)


class AMCRoutineServiceSerializer(serializers.ModelSerializer):
    """Serializer for AMC Routine Service with related data"""
    amc_reference_id = serializers.SerializerMethodField()
    amc_id = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_site_address = serializers.SerializerMethodField()
    customer_job_no = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    customer_latitude = serializers.SerializerMethodField()
    customer_longitude = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = AMCRoutineService
        fields = [
            'id', 'amc_id', 'amc_reference_id', 'service_date', 'block_wing',
            'status', 'status_display', 'note', 'created_at', 'updated_at',
            'customer_name', 'customer_site_address', 'customer_job_no',
            'customer_email', 'customer_phone', 'customer_latitude', 'customer_longitude',
            'employee_id', 'employee_name', 'is_overdue'
        ]
    
    def get_amc_reference_id(self, obj):
        return obj.amc.reference_id if obj.amc else None
    
    def get_amc_id(self, obj):
        return obj.amc.id if obj.amc else None
    
    def get_customer_name(self, obj):
        return getattr(obj.amc.customer, 'site_name', None) if obj.amc and obj.amc.customer else None
    
    def get_customer_site_address(self, obj):
        return getattr(obj.amc.customer, 'site_address', None) if obj.amc and obj.amc.customer else None
    
    def get_customer_job_no(self, obj):
        return getattr(obj.amc.customer, 'job_no', None) if obj.amc and obj.amc.customer else None
    
    def get_customer_email(self, obj):
        return getattr(obj.amc.customer, 'email', None) if obj.amc and obj.amc.customer else None
    
    def get_customer_phone(self, obj):
        return getattr(obj.amc.customer, 'phone', None) if obj.amc and obj.amc.customer else None
    
    def get_customer_latitude(self, obj):
        if obj.amc and obj.amc.customer:
            lat = getattr(obj.amc.customer, 'latitude', None)
            return str(lat) if lat else None
        return None
    
    def get_customer_longitude(self, obj):
        if obj.amc and obj.amc.customer:
            lng = getattr(obj.amc.customer, 'longitude', None)
            return str(lng) if lng else None
        return None
    
    def get_employee_name(self, obj):
        if obj.employee_assign:
            full_name = f"{obj.employee_assign.first_name} {obj.employee_assign.last_name}".strip()
            return full_name if full_name else obj.employee_assign.username
        return None
    
    def get_employee_id(self, obj):
        return obj.employee_assign.id if obj.employee_assign else None
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()

