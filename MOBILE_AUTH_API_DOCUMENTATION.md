# Mobile App Authentication API Documentation

This document describes the REST API endpoints for mobile app authentication using OTP (One-Time Password) verification.

## Overview

The mobile app authentication system allows users who are members of employee groups to login using either their email address or phone number. The system sends an OTP to the provided contact method, and users must verify this OTP to gain access.

## Base URL
```
http://your-domain.com/auth/api/mobile/
```

## Authentication Flow

1. **Generate OTP**: User requests OTP by providing email or phone number
2. **Verify OTP**: User submits the received OTP to complete login
3. **Access Token**: Upon successful verification, user receives an authentication token
4. **API Access**: Use the token in subsequent API requests

## API Endpoints

### 1. Email + Password Login (New)

**Endpoint**: `POST /auth/api/mobile/login/`

**Description**: Logs in the user using email and password (alternative to OTP login) and returns an authentication token.

**Request Body**:
```json
{
    "email": "user@example.com",
    "password": "your_password_here"
}
```

**Response** (Success - 200):
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "phone_number": "+1234567890",
        "is_active": true,
        "date_joined": "2024-01-01T00:00:00Z",
        "last_login": "2024-01-15T10:30:00Z",
        "profile": {
            "phone_number": "+1234567890",
            "branch": "Main Branch",
            "route": "Route A",
            "code": "EMP001",
            "designation": "Manager"
        },
        "groups": ["Employees", "Managers"]
    },
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "message": "Login successful"
}
```

**Response** (Error - 400):
```json
{
    "error": "Invalid email or password"
}
```

**Response** (Error - 403):
```json
{
    "error": "Access denied. Only employees can use mobile app"
}
```

---

### 2. Generate OTP

**Endpoint**: `POST /auth/api/mobile/generate-otp/`

**Description**: Generates and sends an OTP to the user's email or phone number.

**Request Body**:
```json
{
    "email": "user@example.com"
}
```
OR
```json
{
    "phone_number": "+1234567890"
}
```

**Response** (Success - 200):
```json
{
    "message": "OTP sent successfully to your email",
    "otp_type": "email",
    "contact_info": "user@example.com",
    "expires_in_minutes": 10
}
```

**Response** (Error - 404):
```json
{
    "error": "User not found"
}
```

**Response** (Error - 403):
```json
{
    "error": "Access denied. Only employees can use mobile app"
}
```

### 3. Verify OTP and Login

**Endpoint**: `POST /auth/api/mobile/verify-otp/`

**Description**: Verifies the OTP and logs in the user, returning an authentication token.

**Request Body**:
```json
{
    "email": "user@example.com",
    "otp_code": "123456"
}
```
OR
```json
{
    "phone_number": "+1234567890",
    "otp_code": "123456"
}
```

**Response** (Success - 200):
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "is_active": true,
        "date_joined": "2024-01-01T00:00:00Z",
        "profile": {
            "phone_number": "+1234567890",
            "branch": "Main Branch",
            "route": "Route A",
            "code": "EMP001",
            "designation": "Manager"
        },
        "groups": ["Employees", "Managers"]
    },
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "message": "Login successful"
}
```

**Response** (Error - 400):
```json
{
    "error": "OTP expired or maximum attempts exceeded"
}
```

### 4. Resend OTP

**Endpoint**: `POST /auth/api/mobile/resend-otp/`

**Description**: Resends an OTP to the user's email or phone number.

**Request Body**: Same as Generate OTP

**Response**: Same as Generate OTP

### 5. Get User Details

**Endpoint**: `GET /auth/api/mobile/user-details/`

**Description**: Retrieves the authenticated user's details for mobile app display.

**Headers**:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Response** (Success - 200):
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "phone_number": "+1234567890",
        "is_active": true,
        "date_joined": "2024-01-01T00:00:00Z",
        "last_login": "2024-01-15T10:30:00Z",
        "profile": {
            "phone_number": "+1234567890",
            "branch": "Main Branch",
            "route": "Route A",
            "code": "EMP001",
            "designation": "Manager"
        },
        "groups": ["Employees", "Managers"]
    },
    "message": "User details retrieved successfully"
}
```

**Response** (Error - 401):
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**Response** (Error - 403):
```json
{
    "error": "Access denied. Only employees can use mobile app"
}
```

### 6. Logout

**Endpoint**: `POST /auth/api/mobile/logout/`

**Description**: Logs out the user and invalidates their authentication token.

**Headers**:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Response** (Success - 200):
```json
{
    "message": "Logout successful"
}
```

## Error Codes

- **400 Bad Request**: Invalid request data or OTP verification failed
- **403 Forbidden**: User is not in any employee group
- **404 Not Found**: User not found with provided email/phone
- **500 Internal Server Error**: Server error during OTP generation/sending

## Security Features

1. **Employee Group Restriction**: Only users assigned to employee groups can use mobile app
2. **OTP Expiration**: OTPs expire after 10 minutes
3. **Attempt Limiting**: Maximum 3 failed attempts per OTP
4. **Token Authentication**: Secure token-based authentication for API access
5. **CORS Support**: Configured for mobile app cross-origin requests

## Usage Examples

### JavaScript/React Native Example

```javascript
// Generate OTP
const generateOTP = async (email) => {
    const response = await fetch('http://your-domain.com/auth/api/mobile/generate-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email })
    });
    return await response.json();
};

// Verify OTP and Login
const verifyOTP = async (email, otpCode) => {
    const response = await fetch('http://your-domain.com/auth/api/mobile/verify-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            email: email, 
            otp_code: otpCode 
        })
    });
    return await response.json();
};

// Get user details
const getUserDetails = async (token) => {
    const response = await fetch('http://your-domain.com/auth/api/mobile/user-details/', {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Logout
const logout = async (token) => {
    const response = await fetch('http://your-domain.com/auth/api/mobile/logout/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};
```

### Flutter/Dart Example

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class AuthService {
  static const String baseUrl = 'http://your-domain.com/auth/api/mobile';
  
  static Future<Map<String, dynamic>> generateOTP(String email) async {
    final response = await http.post(
      Uri.parse('$baseUrl/generate-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email}),
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> verifyOTP(String email, String otpCode) async {
    final response = await http.post(
      Uri.parse('$baseUrl/verify-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'email': email,
        'otp_code': otpCode,
      }),
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> getUserDetails(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/user-details/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> logout(String token) async {
    final response = await http.post(
      Uri.parse('$baseUrl/logout/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
}
```

## Configuration Notes

1. **Email Settings**: Configure `DEFAULT_FROM_EMAIL` in Django settings for OTP emails
2. **SMS Integration**: The SMS sending function is a placeholder - integrate with services like Twilio, AWS SNS, etc.
3. **CORS**: Update `CORS_ALLOWED_ORIGINS` in settings for production domains
4. **Token Expiration**: Consider implementing token refresh mechanism for long-lived sessions

## Database Models

### OTP Model
- `user`: Foreign key to CustomUser
- `otp_code`: 6-digit OTP code
- `otp_type`: 'email' or 'phone'
- `contact_info`: Email address or phone number
- `created_at`: Timestamp when OTP was created
- `expires_at`: Timestamp when OTP expires (10 minutes)
- `is_used`: Boolean flag for OTP usage
- `attempts`: Number of failed verification attempts

## Admin Interface

The OTP model is available in Django admin for monitoring and management:
- View all generated OTPs
- Monitor failed attempts
- Check OTP usage statistics
- Manual OTP management if needed
