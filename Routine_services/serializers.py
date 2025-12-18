from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import RoutineService
from amc.models import AMCRoutineService


class RoutineServiceSerializer(serializers.Serializer):
    """Serializer for routine service details in mobile API"""
    id = serializers.IntegerField()
    service_date = serializers.DateField()
    service_type = serializers.CharField()
    status = serializers.CharField()
    technician_name = serializers.CharField(allow_null=True)
    code = serializers.CharField(allow_null=True)
    duration = serializers.CharField(allow_null=True)
    service_slip_url = serializers.CharField(allow_null=True)
    is_amc_service = serializers.BooleanField()


class CustomerRoutineServicesResponseSerializer(serializers.Serializer):
    """Serializer for customer routine services dashboard response"""
    last_service = RoutineServiceSerializer(allow_null=True)
    upcoming_service = RoutineServiceSerializer(allow_null=True)
    message = serializers.CharField()


