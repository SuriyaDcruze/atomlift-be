from rest_framework import serializers
from .models import Customer, Route, Branch, ProvinceState, City


class CustomerCreateSerializer(serializers.ModelSerializer):
    province_state = serializers.PrimaryKeyRelatedField(
        queryset=ProvinceState.objects.all(), required=False, allow_null=True
    )
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), required=False, allow_null=True
    )
    routes = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all(), required=False, allow_null=True
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False, allow_null=True
    )
    contact_person_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            # 'site_id',  # Don't need
            'job_no', 'site_name', 'site_address', 'email', 'phone', 'mobile',
            'office_address', 'same_as_site_address', 'contact_person_name', 'designation',
            'pin_code', 'country', 'province_state', 'city', 'sector', 'routes', 'branch',
            'handover_date', 'billing_name', 'uploads_files', 'latitude', 'longitude'
        ]

    def validate(self, attrs):
        site_address = attrs.get('site_address')
        same_as_site_address = attrs.get('same_as_site_address')
        office_address = attrs.get('office_address')
        if same_as_site_address and not site_address:
            raise serializers.ValidationError({'site_address': 'Required when office address is same as site address.'})
        if not attrs.get('site_name'):
            raise serializers.ValidationError({'site_name': 'This field is required.'})
        if not attrs.get('email'):
            raise serializers.ValidationError({'email': 'This field is required.'})
        if not attrs.get('phone'):
            raise serializers.ValidationError({'phone': 'This field is required.'})
        return attrs

    def create(self, validated_data):
        same_as_site_address = validated_data.get('same_as_site_address')
        if same_as_site_address:
            validated_data['office_address'] = validated_data.get('site_address')
        customer = Customer.objects.create(**validated_data)
        return customer


class CustomerListSerializer(serializers.ModelSerializer):
    branch_name = serializers.SerializerMethodField()
    route_name = serializers.SerializerMethodField()
    province_state_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'reference_id', 
            # 'site_id',  # Don't need
            'job_no', 'site_name', 'site_address',
            'email', 'phone', 'mobile', 'contact_person_name', 'designation',
            'city_name', 'sector', 'branch_name', 'route_name', 'province_state_name',
            'latitude', 'longitude'
        ]

    def get_branch_name(self, obj):
        return getattr(obj.branch, 'value', None)

    def get_route_name(self, obj):
        return getattr(obj.routes, 'value', None)

    def get_province_state_name(self, obj):
        return getattr(obj.province_state, 'value', None)

    def get_city_name(self, obj):
        return getattr(obj.city, 'value', None)


