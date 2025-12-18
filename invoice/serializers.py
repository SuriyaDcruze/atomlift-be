from rest_framework import serializers
from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice items"""
    item_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = ['id', 'item_name', 'rate', 'qty', 'tax', 'total']
    
    def get_item_name(self, obj):
        return getattr(obj.item, 'name', 'N/A') if obj.item else 'N/A'


class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer for listing invoices for mobile app"""
    customer_name = serializers.SerializerMethodField()
    amc_type_name = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    start_date_str = serializers.SerializerMethodField()
    due_date_str = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'reference_id', 'customer_name', 'amc_type_name',
            'start_date', 'start_date_str', 'due_date', 'due_date_str',
            'discount', 'payment_term', 'status', 'status_display',
            'total_amount', 'items'
        ]
    
    def get_customer_name(self, obj):
        return getattr(obj.customer, 'site_name', 'N/A') if obj.customer else 'N/A'
    
    def get_amc_type_name(self, obj):
        return getattr(obj.amc_type, 'name', 'N/A') if obj.amc_type else 'N/A'
    
    def get_total_amount(self, obj):
        return float(obj.get_total())
    
    def get_start_date_str(self, obj):
        return obj.start_date.strftime('%Y-%m-%d') if obj.start_date else None
    
    def get_due_date_str(self, obj):
        return obj.due_date.strftime('%Y-%m-%d') if obj.due_date else None
    
    def get_status_display(self, obj):
        return obj.get_status_display()


