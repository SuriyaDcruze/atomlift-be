from rest_framework import serializers
from .models import AMC, AMCType, PaymentTerms
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
            'customer', 'amcname', 'latitude', 'equipment_no', 'invoice_frequency',
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
            'id', 'reference_id', 'amcname', 'latitude', 'equipment_no',
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

