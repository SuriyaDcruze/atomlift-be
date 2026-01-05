from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import SubCustomer
from .serializers import (
    SubCustomerSerializer,
    SubCustomerCreateSerializer,
    SubCustomerUpdateSerializer,
    SubCustomerListSerializer
)
from customer.models import Customer, CustomerOTP
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_subcustomer(request):
    """
    Create a new sub-customer.
    Requires customer email to verify the customer is logged in.
    The customer email is obtained from the request (after OTP verification in mobile app).
    """
    try:
        customer_email = request.data.get('customer_email')
        if not customer_email:
            return Response(
                {'error': 'customer_email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify customer exists
        try:
            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create serializer with customer context
        serializer = SubCustomerCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Check if sub-customer with same email already exists for this customer
            email = serializer.validated_data.get('email')
            if SubCustomer.objects.filter(customer=customer, email=email).exists():
                return Response(
                    {'error': f'Sub-customer with email {email} already exists for this customer'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create sub-customer
            subcustomer = serializer.save(
                customer=customer,
                created_by=customer_email
            )
            
            # Return full sub-customer details
            response_serializer = SubCustomerSerializer(subcustomer)
            return Response(
                {
                    'message': 'Sub-customer created successfully',
                    'subcustomer': response_serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating sub-customer: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def list_subcustomers(request):
    """
    List all sub-customers for a specific customer.
    Requires customer_email query parameter.
    """
    try:
        customer_email = request.query_params.get('customer_email')
        if not customer_email:
            return Response(
                {'error': 'customer_email query parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get customer
        try:
            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all sub-customers for this customer
        subcustomers = SubCustomer.objects.filter(customer=customer).order_by('-created_at')
        
        # Optional filter for active only
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            subcustomers = subcustomers.filter(is_active=True)
        
        serializer = SubCustomerListSerializer(subcustomers, many=True)
        return Response(
            {
                'count': subcustomers.count(),
                'subcustomers': serializer.data
            }, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error listing sub-customers: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def subcustomer_detail(request, subcustomer_id):
    """
    Get details of a specific sub-customer.
    Requires customer_email query parameter to verify ownership.
    """
    try:
        customer_email = request.query_params.get('customer_email')
        if not customer_email:
            return Response(
                {'error': 'customer_email query parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get customer
        try:
            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sub-customer and verify ownership
        try:
            subcustomer = SubCustomer.objects.get(id=subcustomer_id, customer=customer)
        except SubCustomer.DoesNotExist:
            return Response(
                {'error': 'Sub-customer not found or does not belong to this customer'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubCustomerSerializer(subcustomer)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting sub-customer detail: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def update_subcustomer(request, subcustomer_id):
    """
    Update a sub-customer.
    Requires customer_email in request data to verify ownership.
    """
    try:
        customer_email = request.data.get('customer_email')
        if not customer_email:
            return Response(
                {'error': 'customer_email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get customer
        try:
            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sub-customer and verify ownership
        try:
            subcustomer = SubCustomer.objects.get(id=subcustomer_id, customer=customer)
        except SubCustomer.DoesNotExist:
            return Response(
                {'error': 'Sub-customer not found or does not belong to this customer'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update sub-customer
        serializer = SubCustomerUpdateSerializer(subcustomer, data=request.data, partial=True)
        if serializer.is_valid():
            # Check if email is being changed and if it conflicts
            if 'email' in serializer.validated_data:
                new_email = serializer.validated_data['email']
                if SubCustomer.objects.filter(customer=customer, email=new_email).exclude(id=subcustomer_id).exists():
                    return Response(
                        {'error': f'Sub-customer with email {new_email} already exists for this customer'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer.save()
            
            # Return updated sub-customer
            response_serializer = SubCustomerSerializer(subcustomer)
            return Response(
                {
                    'message': 'Sub-customer updated successfully',
                    'subcustomer': response_serializer.data
                }, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error updating sub-customer: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_subcustomer(request, subcustomer_id):
    """
    Delete a sub-customer.
    Requires customer_email query parameter to verify ownership.
    """
    try:
        customer_email = request.query_params.get('customer_email')
        if not customer_email:
            return Response(
                {'error': 'customer_email query parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get customer
        try:
            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sub-customer and verify ownership
        try:
            subcustomer = SubCustomer.objects.get(id=subcustomer_id, customer=customer)
        except SubCustomer.DoesNotExist:
            return Response(
                {'error': 'Sub-customer not found or does not belong to this customer'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        subcustomer.delete()
        return Response(
            {'message': 'Sub-customer deleted successfully'}, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error deleting sub-customer: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def subcustomer_login(request):
    """
    Login for sub-customer.
    Sub-customers use the customer's email + OTP verification, but with sub-customer identification.
    This ensures sub-customers can only access customer user apps, not admin/technician apps.
    
    Request body should contain:
    - customer_email: The parent customer's email
    - subcustomer_email: The sub-customer's email
    - otp_code: OTP code for verification
    """
    try:
        customer_email = request.data.get('customer_email')
        subcustomer_email = request.data.get('subcustomer_email')
        otp_code = request.data.get('otp_code')
        
        if not customer_email:
            return Response(
                {'error': 'customer_email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not subcustomer_email:
            return Response(
                {'error': 'subcustomer_email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not otp_code:
            return Response(
                {'error': 'otp_code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get customer
        try:
            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sub-customer
        try:
            subcustomer = SubCustomer.objects.get(
                customer=customer, 
                email=subcustomer_email,
                is_active=True
            )
        except SubCustomer.DoesNotExist:
            return Response(
                {'error': 'Sub-customer not found or is not active'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if sub-customer has access permission
        if not subcustomer.can_access_app:
            return Response(
                {'error': 'This sub-customer does not have permission to access the app'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify OTP using customer's email (sub-customers use customer's credentials)
        is_valid, message = CustomerOTP.verify_otp(customer, otp_code, customer_email)
        
        if not is_valid:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return customer data (sub-customer accesses with customer's credentials)
        # but include sub-customer info to identify who is logged in
        from customer.serializers import CustomerLoginSerializer
        customer_serializer = CustomerLoginSerializer(customer)
        
        # Include sub-customer information
        from .serializers import SubCustomerSerializer
        subcustomer_serializer = SubCustomerSerializer(subcustomer)
        
        response_data = {
            'customer': customer_serializer.data,
            'subcustomer': subcustomer_serializer.data,
            'is_subcustomer': True,
            'message': 'Login successful as sub-customer'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in sub-customer login: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
