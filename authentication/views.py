from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import logging

from .models import CustomUser, OTP
from .serializers import (
    GenerateOTPRequestSerializer, 
    VerifyOTPRequestSerializer,
    MobileLoginResponseSerializer,
    OTPSendResponseSerializer,
    UserSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


def send_otp_email(email, otp_code):
    """Send OTP via email"""
    try:
        subject = 'Your Mobile App Login OTP'
        message = f'Your OTP for mobile app login is: {otp_code}\n\nThis OTP is valid for 10 minutes.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email,'rkpavi06@gmail.com']
        
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        return False


def send_otp_sms(phone_number, otp_code):
    """Send OTP via SMS - placeholder for SMS service integration"""
    # This is a placeholder. In production, integrate with SMS service like Twilio, AWS SNS, etc.
    logger.info(f"SMS OTP for {phone_number}: {otp_code}")
    # For now, we'll just log it. Replace with actual SMS service.
    return True


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_otp(request):
    """
    Generate and send OTP for mobile app login
    Only users in employee groups can use this API
    """
    serializer = GenerateOTPRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data.get('email')
    phone_number = serializer.validated_data.get('phone_number')
    
    try:
        # Find user by email or phone number
        if email:
            user = User.objects.get(email=email, is_active=True)
            contact_info = email
            otp_type = 'email'
        else:
            # Try to find user by phone number in profile or user model
            user = User.objects.filter(
                Q(phone_number=phone_number) | 
                Q(profile__phone_number=phone_number),
                is_active=True
            ).first()
            
            if not user:
                return Response(
                    {'error': 'User not found with this phone number'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            contact_info = phone_number
            otp_type = 'phone'
        
        # Check if user is in any employee group
        if not user.groups.exists():
            return Response(
                {'error': 'Access denied. Only employees can use mobile app'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate OTP
        otp = OTP.generate_otp(user, otp_type, contact_info)
        
        # Send OTP
        if otp_type == 'email':
            success = send_otp_email(email, otp.otp_code)
        else:
            success = send_otp_sms(phone_number, otp.otp_code)
        
        if not success:
            return Response(
                {'error': 'Failed to send OTP. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_data = {
            'message': f'OTP sent successfully to your {otp_type}',
            'otp_type': otp_type,
            'contact_info': contact_info,
            'expires_in_minutes': 10
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error generating OTP: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_and_login(request):
    """
    Verify OTP and login user for mobile app
    """
    serializer = VerifyOTPRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data.get('email')
    phone_number = serializer.validated_data.get('phone_number')
    otp_code = serializer.validated_data.get('otp_code')
    
    try:
        # Find user
        if email:
            user = User.objects.get(email=email, is_active=True)
            otp_type = 'email'
        else:
            user = User.objects.filter(
                Q(phone_number=phone_number) | 
                Q(profile__phone_number=phone_number),
                is_active=True
            ).first()
            
            if not user:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            otp_type = 'phone'
        
        # Check if user is in any employee group
        if not user.groups.exists():
            return Response(
                {'error': 'Access denied. Only employees can use mobile app'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify OTP
        is_valid, message = OTP.verify_otp(user, otp_code, otp_type)
        
        if not is_valid:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get token for user
        token, created = Token.objects.get_or_create(user=user)
        
        # Prepare response data
        user_serializer = UserSerializer(user)
        response_data = {
            'user': user_serializer.data,
            'token': token.key,
            'message': 'Login successful'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """
    Resend OTP for mobile app login
    """
    serializer = GenerateOTPRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data.get('email')
    phone_number = serializer.validated_data.get('phone_number')
    
    try:
        # Find user
        if email:
            user = User.objects.get(email=email, is_active=True)
            contact_info = email
            otp_type = 'email'
        else:
            user = User.objects.filter(
                Q(phone_number=phone_number) | 
                Q(profile__phone_number=phone_number),
                is_active=True
            ).first()
            
            if not user:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            contact_info = phone_number
            otp_type = 'phone'
        
        # Check if user is in any employee group
        if not user.groups.exists():
            return Response(
                {'error': 'Access denied. Only employees can use mobile app'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate new OTP
        otp = OTP.generate_otp(user, otp_type, contact_info)
        
        # Send OTP
        if otp_type == 'email':
            success = send_otp_email(email, otp.otp_code)
        else:
            success = send_otp_sms(phone_number, otp.otp_code)
        
        if not success:
            return Response(
                {'error': 'Failed to send OTP. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_data = {
            'message': f'OTP resent successfully to your {otp_type}',
            'otp_type': otp_type,
            'contact_info': contact_info,
            'expires_in_minutes': 10
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error resending OTP: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def logout(request):
    """
    Logout user and delete token
    """
    try:
        # Delete the token
        request.user.auth_token.delete()
        return Response(
            {'message': 'Logout successful'}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return Response(
            {'error': 'Logout failed'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    """
    Get authenticated user details for mobile app
    """
    try:
        user = request.user
        
        # Check if user is in any employee group
        if not user.groups.exists():
            return Response(
                {'error': 'Access denied. Only employees can use mobile app'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        response_data = {
            'user': user_serializer.data,
            'message': 'User details retrieved successfully'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving user details: {e}")
        return Response(
            {'error': 'Failed to retrieve user details'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
