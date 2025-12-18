from rest_framework import serializers
from .models import Quotation


class QuotationListSerializer(serializers.ModelSerializer):
    """Serializer for listing quotations for mobile app"""
    customer_name = serializers.SerializerMethodField()
    amc_type_name = serializers.SerializerMethodField()
    date_str = serializers.SerializerMethodField()
    lifts_list = serializers.SerializerMethodField()
    sales_executive_name = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Quotation
        fields = [
            'id', 'reference_id', 'customer_name', 'amc_type_name',
            'type', 'type_display', 'year_of_make', 'date', 'date_str',
            'remark', 'other_remark', 'lifts_list', 'sales_executive_name'
        ]
    
    def get_customer_name(self, obj):
        return getattr(obj.customer, 'site_name', 'N/A') if obj.customer else 'N/A'
    
    def get_amc_type_name(self, obj):
        return getattr(obj.amc_type, 'name', 'N/A') if obj.amc_type else 'N/A'
    
    def get_date_str(self, obj):
        return obj.date.strftime('%Y-%m-%d') if obj.date else None
    
    def get_lifts_list(self, obj):
        """Return list of lift codes/names"""
        lifts = obj.lifts.all()
        return [f"{lift.lift_code or lift.name}" for lift in lifts] if lifts else []
    
    def get_sales_executive_name(self, obj):
        if obj.sales_service_executive:
            full_name = f"{obj.sales_service_executive.first_name} {obj.sales_service_executive.last_name}".strip()
            return full_name if full_name else obj.sales_service_executive.username
        return 'N/A'
    
    def get_type_display(self, obj):
        return obj.get_type_display() if hasattr(obj, 'get_type_display') else obj.type


