# Mobile Complaints API Documentation

This document describes the REST API endpoints for mobile app complaint management. These APIs allow authenticated employees to view and manage their assigned complaints.

## Overview

The mobile complaints system provides APIs for employees to:
- View complaints assigned to them
- Get detailed complaint information
- Update complaint status and technician remarks
- Access complaint types and priorities

## Base URL
```
http://your-domain.com/complaints/api/mobile/
```

## Authentication

All endpoints require authentication using the token received from the mobile authentication API:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## API Endpoints

### 1. Get Assigned Complaints

**Endpoint**: `GET /complaints/api/mobile/complaints/`

**Description**: Retrieves all complaints assigned to the authenticated user with pagination and filtering options.

**Query Parameters**:
- `status` (optional): Filter by complaint status (`open`, `in_progress`, `closed`)
- `priority` (optional): Filter by priority ID
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Number of items per page (default: 20)

**Example Request**:
```
GET /complaints/api/mobile/complaints/?status=open&page=1&page_size=10
```

**Response** (Success - 200):
```json
{
    "complaints": [
        {
            "id": 1,
            "reference": "CMP1001",
            "complaint_type": {
                "id": 1,
                "name": "Lift Not Working"
            },
            "date": "2024-01-15",
            "customer": {
                "id": 1,
                "reference_id": "CUST001",
                "site_id": "SITE001",
                "job_no": "JOB001",
                "site_name": "ABC Building",
                "site_address": "123 Main Street, City",
                "email": "contact@abcbuilding.com",
                "phone": "+1234567890",
                "mobile": "+1234567891",
                "contact_person_name": "John Doe",
                "designation": "Manager",
                "city": "New York",
                "branch": "Main Branch",
                "routes": "Route A"
            },
            "contact_person_name": "John Doe",
            "contact_person_mobile": "+1234567890",
            "block_wing": "Block A, Wing 1",
            "status": "open",
            "lift_info": "Lift 1 - Ground Floor",
            "complaint_templates": "Lift not responding, Door not opening",
            "assign_to_name": "Technician Name",
            "priority": {
                "id": 1,
                "name": "High"
            },
            "subject": "Lift Not Working",
            "message": "Lift is not responding to calls",
            "technician_remark": "",
            "solution": "",
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z",
            "days_since_created": 0
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 3,
        "total_count": 45,
        "has_next": true,
        "has_previous": false
    },
    "message": "Assigned complaints retrieved successfully"
}
```

### 2. Get Complaint Details

**Endpoint**: `GET /complaints/api/mobile/complaints/{reference}/`

**Description**: Retrieves detailed information about a specific complaint including assignment history.

**Example Request**:
```
GET /complaints/api/mobile/complaints/CMP1001/
```

**Response** (Success - 200):
```json
{
    "complaint": {
        "id": 1,
        "reference": "CMP1001",
        "complaint_type": {
            "id": 1,
            "name": "Lift Not Working"
        },
        "date": "2024-01-15",
        "customer": {
            "id": 1,
            "reference_id": "CUST001",
            "site_id": "SITE001",
            "job_no": "JOB001",
            "site_name": "ABC Building",
            "site_address": "123 Main Street, City",
            "email": "contact@abcbuilding.com",
            "phone": "+1234567890",
            "mobile": "+1234567891",
            "contact_person_name": "John Doe",
            "designation": "Manager",
            "city": "New York",
            "branch": "Main Branch",
            "routes": "Route A"
        },
        "contact_person_name": "John Doe",
        "contact_person_mobile": "+1234567890",
        "block_wing": "Block A, Wing 1",
        "status": "open",
        "lift_info": "Lift 1 - Ground Floor",
        "complaint_templates": "Lift not responding, Door not opening",
        "assign_to_name": "Technician Name",
        "priority": {
            "id": 1,
            "name": "High"
        },
        "subject": "Lift Not Working",
        "message": "Lift is not responding to calls",
        "technician_remark": "",
        "solution": "",
        "created": "2024-01-15T10:30:00Z",
        "updated": "2024-01-15T10:30:00Z",
        "days_since_created": 0,
        "assignment_history": [
            {
                "id": 1,
                "assigned_to_name": "Technician Name",
                "assigned_by_name": "Admin User",
                "assignment_date": "2024-01-15T10:30:00Z",
                "subject": "Complaint assigned",
                "message": "Please resolve this complaint as soon as possible",
                "created": "2024-01-15T10:30:00Z"
            }
        ],
        "status_history": [
            {
                "id": 1,
                "old_status": "open",
                "new_status": "in_progress",
                "changed_by_name": "Technician Name",
                "change_reason": "Started working on the complaint",
                "technician_remark": "Inspected the lift",
                "solution": "",
                "changed_at": "2024-01-15T11:00:00Z",
                "changed_from_mobile": true
            }
        ]
    },
    "message": "Complaint details retrieved successfully"
}
```

### 3. Update Complaint Status

**Endpoint**: `PATCH /complaints/api/mobile/complaints/{reference}/update/`

**Description**: Updates complaint status, technician remarks, and solution.

**Request Body**:
```json
{
    "status": "in_progress",
    "technician_remark": "Inspected the lift. Found issue with door mechanism.",
    "solution": "Replaced door mechanism. Lift is now working properly.",
    "change_reason": "Started working on the complaint after inspection"
}
```

**Response** (Success - 200):
```json
{
    "complaint": {
        "id": 1,
        "reference": "CMP1001",
        "status": "in_progress",
        "technician_remark": "Inspected the lift. Found issue with door mechanism.",
        "solution": "Replaced door mechanism. Lift is now working properly.",
        // ... other complaint fields
    },
    "message": "Complaint updated successfully"
}
```

### 4. Get Complaint Types

**Endpoint**: `GET /complaints/api/mobile/complaint-types/`

**Description**: Retrieves all available complaint types.

**Response** (Success - 200):
```json
{
    "complaint_types": [
        {
            "id": 1,
            "name": "Lift Not Working"
        },
        {
            "id": 2,
            "name": "Door Not Opening"
        },
        {
            "id": 3,
            "name": "Stuck Between Floors"
        }
    ],
    "message": "Complaint types retrieved successfully"
}
```

### 5. Get Complaint Priorities

**Endpoint**: `GET /complaints/api/mobile/complaint-priorities/`

**Description**: Retrieves all available complaint priorities.

**Response** (Success - 200):
```json
{
    "priorities": [
        {
            "id": 1,
            "name": "High"
        },
        {
            "id": 2,
            "name": "Medium"
        },
        {
            "id": 3,
            "name": "Low"
        }
    ],
    "message": "Complaint priorities retrieved successfully"
}
```

## Error Responses

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "Access denied. Only employees can use mobile app"
}
```

### 404 Not Found
```json
{
    "error": "Complaint not found"
}
```

### 500 Internal Server Error
```json
{
    "error": "Failed to retrieve assigned complaints"
}
```

## Usage Examples

### JavaScript/React Native Example

```javascript
// Get assigned complaints
const getAssignedComplaints = async (token, filters = {}) => {
    const queryParams = new URLSearchParams(filters);
    const response = await fetch(`http://your-domain.com/complaints/api/mobile/complaints/?${queryParams}`, {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Get complaint details
const getComplaintDetail = async (token, reference) => {
    const response = await fetch(`http://your-domain.com/complaints/api/mobile/complaints/${reference}/`, {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Update complaint status
const updateComplaintStatus = async (token, reference, updateData) => {
    const response = await fetch(`http://your-domain.com/complaints/api/mobile/complaints/${reference}/update/`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData)
    });
    return await response.json();
};

// Usage examples
const complaints = await getAssignedComplaints(token, { status: 'open', page: 1 });
const complaintDetail = await getComplaintDetail(token, 'CMP1001');
const updateResult = await updateComplaintStatus(token, 'CMP1001', {
    status: 'in_progress',
    technician_remark: 'Started working on the issue',
    change_reason: 'Beginning inspection and repair work'
});
```

### Flutter/Dart Example

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ComplaintsService {
  static const String baseUrl = 'http://your-domain.com/complaints/api/mobile';
  
  static Future<Map<String, dynamic>> getAssignedComplaints(String token, {Map<String, String>? filters}) async {
    String queryParams = '';
    if (filters != null && filters.isNotEmpty) {
      queryParams = '?' + filters.entries.map((e) => '${e.key}=${e.value}').join('&');
    }
    
    final response = await http.get(
      Uri.parse('$baseUrl/complaints/$queryParams'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> getComplaintDetail(String token, String reference) async {
    final response = await http.get(
      Uri.parse('$baseUrl/complaints/$reference/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> updateComplaintStatus(String token, String reference, Map<String, dynamic> updateData) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/complaints/$reference/update/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: json.encode(updateData),
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> getComplaintTypes(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/complaint-types/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> getComplaintPriorities(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/complaint-priorities/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
}
```

## Real-Time Admin Updates

When users update complaint status through the mobile app, the changes are **automatically reflected** in the Wagtail admin interface:

### ✅ **What Happens Automatically**
1. **Status Changes**: When a user changes status from `open` → `in_progress` → `closed`
2. **Technician Remarks**: All remarks added by technicians are visible in admin
3. **Solutions**: Solutions provided by technicians are recorded
4. **Timestamps**: All changes are timestamped with exact time
5. **User Tracking**: Admin can see which technician made the changes
6. **Change History**: Complete audit trail of all status changes

### 📊 **Admin Interface Features**
- **Status History View**: New "Status History" section in Wagtail admin
- **Real-time Updates**: No refresh needed - changes appear immediately
- **Mobile Tracking**: Admin can see which changes came from mobile app
- **Complete Audit Trail**: Track who changed what and when
- **Filtering**: Filter by mobile changes, status, date, etc.

## Security Features

1. **Token Authentication**: All endpoints require valid authentication token
2. **Employee Group Restriction**: Only users in employee groups can access these APIs
3. **Assignment Validation**: Users can only access complaints assigned to them
4. **Input Validation**: All input data is validated before processing
5. **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
6. **Status Change Tracking**: Complete audit trail of all status changes
7. **Mobile App Identification**: All mobile changes are clearly marked

## Data Models

### Complaint Status Options
- `open`: Complaint is newly created and not yet started
- `in_progress`: Complaint is being worked on
- `closed`: Complaint has been resolved

### Complaint Fields
- **Basic Info**: reference, complaint_type, date, priority, status
- **Customer Info**: customer details, contact person, location
- **Technical Info**: lift_info, complaint_templates, technician_remark, solution
- **Assignment Info**: assign_to, assignment_history
- **Timestamps**: created, updated, days_since_created

## Notes

1. **Pagination**: All list endpoints support pagination for better performance
2. **Filtering**: Complaints can be filtered by status and priority
3. **Assignment History**: Detailed complaint view includes assignment history
4. **Real-time Updates**: Status updates are immediately reflected in the system
5. **Mobile Optimized**: All responses are optimized for mobile app consumption
