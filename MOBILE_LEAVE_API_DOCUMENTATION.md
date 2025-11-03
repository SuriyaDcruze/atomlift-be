# Mobile App - Leave Request API Documentation

## Base URL
All endpoints are prefixed with: `/employeeleave/`

**Full Base URL:** `https://your-domain.com/employeeleave/`

---

## Authentication
All APIs require **Token Authentication**. Include the token in the Authorization header:

```
Authorization: Token <your_auth_token>
```

---

## 📱 **USER ENDPOINTS** (For Employees)

### 1. **Create Leave Request**
**POST** `/employeeleave/api/leave/create/`

**Description:** Create a new leave request (status will be 'pending' by default)

**Request Body:**
```json
{
  "half_day": false,
  "leave_type": "casual",
  "from_date": "2024-01-15",
  "to_date": "2024-01-17",
  "reason": "Personal work",
  "email": "employee@example.com"
}
```

**Field Validations:**
- `half_day`: Boolean (true/false)
- `leave_type`: One of: `"casual"`, `"sick"`, `"earned"`, `"unpaid"`, `"other"`
- `from_date`: Date in format `YYYY-MM-DD`
- `to_date`: Date in format `YYYY-MM-DD` (must be >= from_date)
- `reason`: String (optional)
- `email`: Valid email address

**Success Response (201 Created):**
```json
{
  "message": "Leave request created successfully",
  "leave_request": {
    "id": 1,
    "user": 5,
    "user_detail": {
      "id": 5,
      "email": "employee@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "phone_number": "+1234567890"
    },
    "half_day": false,
    "leave_type": "casual",
    "leave_type_display": "Casual Leave",
    "from_date": "2024-01-15",
    "to_date": "2024-01-17",
    "reason": "Personal work",
    "email": "employee@example.com",
    "status": "pending",
    "status_display": "Pending",
    "admin_remarks": null,
    "created_at": "2024-01-10T10:30:00Z",
    "updated_at": "2024-01-10T10:30:00Z"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Validation failed",
  "details": {
    "to_date": ["To date must be after or equal to from date."],
    "email": ["Enter a valid email address."]
  }
}
```

---

### 2. **List User's Leave Requests**
**GET** `/employeeleave/api/leave/list/`

**Description:** Get all leave requests for the authenticated user

**Query Parameters (Optional):**
- `status`: Filter by status (`pending`, `approved`, `rejected`)
- `leave_type`: Filter by leave type (`casual`, `sick`, `earned`, `unpaid`, `other`)
- `q`: Search term (searches in leave_type, reason, status)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Example Request:**
```
GET /employeeleave/api/leave/list/?status=pending&leave_type=casual&page=1
```

**Success Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://your-domain.com/employeeleave/api/leave/list/?page=2",
  "previous": null,
  "results": {
    "leave_requests": [
      {
        "id": 1,
        "user": 5,
        "user_detail": {
          "id": 5,
          "email": "employee@example.com",
          "first_name": "John",
          "last_name": "Doe",
          "full_name": "John Doe",
          "phone_number": "+1234567890"
        },
        "half_day": false,
        "leave_type": "casual",
        "leave_type_display": "Casual Leave",
        "from_date": "2024-01-15",
        "to_date": "2024-01-17",
        "reason": "Personal work",
        "email": "employee@example.com",
        "status": "pending",
        "status_display": "Pending",
        "admin_remarks": null,
        "created_at": "2024-01-10T10:30:00Z",
        "updated_at": "2024-01-10T10:30:00Z"
      }
    ]
  }
}
```

---

### 3. **Get Leave Request Detail**
**GET** `/employeeleave/api/leave/<id>/`

**Description:** Get details of a specific leave request (users can only view their own requests)

---

### 4. **Update Leave Request (User)**
**PATCH/PUT** `/employeeleave/api/leave/<id>/update/`

**Description:** Update your own leave request (only if status is 'pending')

**Request Body (All fields optional - partial update allowed):**
```json
{
  "half_day": true,
  "leave_type": "sick",
  "from_date": "2024-01-20",
  "to_date": "2024-01-21",
  "reason": "Updated reason - feeling unwell",
  "email": "updated@example.com"
}
```

**Important Rules:**
- Users can only update their own leave requests
- Only leave requests with `status = "pending"` can be updated
- Once approved or rejected, the leave request cannot be modified by the user

**Example Request:**
```
PATCH /employeeleave/api/leave/1/update/
```

**Success Response (200 OK):**
```json
{
  "message": "Leave request updated successfully",
  "leave_request": {
    "id": 1,
    "user": 5,
    "user_detail": {
      "id": 5,
      "email": "employee@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "phone_number": "+1234567890"
    },
    "half_day": true,
    "leave_type": "sick",
    "leave_type_display": "Sick Leave",
    "from_date": "2024-01-20",
    "to_date": "2024-01-21",
    "reason": "Updated reason - feeling unwell",
    "email": "updated@example.com",
    "status": "pending",
    "status_display": "Pending",
    "admin_remarks": null,
    "created_at": "2024-01-10T10:30:00Z",
    "updated_at": "2024-01-10T15:45:00Z"
  }
}
```

**Error Responses:**

**403 Forbidden (Not Owner):**
```json
{
  "error": "Access denied. You can only update your own leave requests."
}
```

**400 Bad Request (Already Processed):**
```json
{
  "error": "Cannot update leave request. Current status is 'approved'. Only pending leave requests can be updated."
}
```

---

### 5. **Delete Leave Request (User)**
**DELETE** `/employeeleave/api/leave/<id>/delete/`

**Description:** Delete your own leave request (only if status is 'pending')

**Important Rules:**
- Users can only delete their own leave requests
- Only leave requests with `status = "pending"` can be deleted
- Once approved or rejected, the leave request cannot be deleted

**Example Request:**
```
DELETE /employeeleave/api/leave/1/delete/
```

**Success Response (200 OK):**
```json
{
  "message": "Leave request deleted successfully",
  "deleted_leave_request": {
    "id": 1,
    "leave_type": "casual",
    "from_date": "2024-01-15",
    "to_date": "2024-01-17"
  }
}
```

**Error Responses:**

**403 Forbidden (Not Owner):**
```json
{
  "error": "Access denied. You can only delete your own leave requests."
}
```

**400 Bad Request (Already Processed):**
```json
{
  "error": "Cannot delete leave request. Current status is 'approved'. Only pending leave requests can be deleted."
}
```

---

## 🔐 **ADMIN ENDPOINTS** (For Admin/Staff Users)

### 6. **List All Leave Requests (Admin)**
**GET** `/employeeleave/api/leave/admin/list/`

**Description:** Get all leave requests from all users (Admin only)

**Success Response (200 OK):**
```json
{
  "leave_request": {
    "id": 1,
    "user": 5,
    "user_detail": {
      "id": 5,
      "email": "employee@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "phone_number": "+1234567890"
    },
    "half_day": false,
    "leave_type": "casual",
    "leave_type_display": "Casual Leave",
    "from_date": "2024-01-15",
    "to_date": "2024-01-17",
    "reason": "Personal work",
    "email": "employee@example.com",
    "status": "approved",
    "status_display": "Approved",
    "admin_remarks": "Leave approved. Enjoy your time off!",
    "created_at": "2024-01-10T10:30:00Z",
    "updated_at": "2024-01-10T12:45:00Z"
  }
}
```

**Error Response (403 Forbidden):**
```json
{
  "error": "Access denied. You can only view your own leave requests."
}
```

---

## 🔐 **ADMIN ENDPOINTS** (For Admin/Staff Users)

### 4. **List All Leave Requests (Admin)**
**GET** `/employeeleave/api/leave/admin/list/`

**Description:** Get all leave requests from all users (Admin only)

**Query Parameters (Optional):**
- `status`: Filter by status (`pending`, `approved`, `rejected`)
- `leave_type`: Filter by leave type (`casual`, `sick`, `earned`, `unpaid`, `other`)
- `user_id`: Filter by specific user ID
- `q`: Search term (searches in user name, email, leave_type, reason, status)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Example Request:**
```
GET /employeeleave/api/leave/admin/list/?status=pending&page=1
```

**Success Response (200 OK):**
```json
{
  "count": 50,
  "next": "http://your-domain.com/employeeleave/api/leave/admin/list/?page=2",
  "previous": null,
  "results": {
    "leave_requests": [
      {
        "id": 1,
        "user": 5,
        "user_detail": {
          "id": 5,
          "email": "employee@example.com",
          "first_name": "John",
          "last_name": "Doe",
          "full_name": "John Doe",
          "phone_number": "+1234567890"
        },
        "half_day": false,
        "leave_type": "casual",
        "leave_type_display": "Casual Leave",
        "from_date": "2024-01-15",
        "to_date": "2024-01-17",
        "reason": "Personal work",
        "email": "employee@example.com",
        "status": "pending",
        "status_display": "Pending",
        "admin_remarks": null,
        "created_at": "2024-01-10T10:30:00Z",
        "updated_at": "2024-01-10T10:30:00Z"
      }
    ]
  }
}
```

**Error Response (403 Forbidden):**
```json
{
  "error": "Access denied. Only admins can view all leave requests."
}
```

---

### 7. **Update Leave Request Status (Admin)**
**PATCH** `/employeeleave/api/leave/admin/<id>/update/`

**Description:** Approve or reject a leave request (Admin only)

**Request Body:**
```json
{
  "status": "approved",
  "admin_remarks": "Leave approved. Have a good time!"
}
```

**OR**

```json
{
  "status": "rejected",
  "admin_remarks": "Leave rejected due to project deadline."
}
```

**Field Validations:**
- `status`: Required. Must be `"approved"` or `"rejected"`
- `admin_remarks`: Optional. String with admin's remarks/notes

**Example Request:**
```
PATCH /employeeleave/api/leave/admin/1/update/
```

**Success Response (200 OK):**
```json
{
  "message": "Leave request status updated successfully",
  "leave_request": {
    "id": 1,
    "user": 5,
    "user_detail": {
      "id": 5,
      "email": "employee@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "phone_number": "+1234567890"
    },
    "half_day": false,
    "leave_type": "casual",
    "leave_type_display": "Casual Leave",
    "from_date": "2024-01-15",
    "to_date": "2024-01-17",
    "reason": "Personal work",
    "email": "employee@example.com",
    "status": "approved",
    "status_display": "Approved",
    "admin_remarks": "Leave approved. Have a good time!",
    "created_at": "2024-01-10T10:30:00Z",
    "updated_at": "2024-01-10T14:20:00Z"
  }
}
```

**Error Responses:**

**403 Forbidden (Not Admin):**
```json
{
  "error": "Access denied. Only admins can update leave request status."
}
```

**400 Bad Request (Already Processed):**
```json
{
  "error": "Cannot change status. Current status is 'approved'. Only pending requests can be updated."
}
```

---

## 🔒 **Edit/Delete Restrictions**

### Users can only:
- ✅ Edit/Delete their own leave requests
- ✅ Edit/Delete leave requests with `status = "pending"`
- ❌ Cannot edit/delete if status is `"approved"` or `"rejected"`

### Important Notes:
- Once a leave request is approved or rejected by admin, it cannot be modified or deleted by the user
- Users must edit or delete their leave requests before admin processes them
- If you need to change an approved/rejected leave request, contact your administrator

---

## 📋 **Leave Type Options**
- `"casual"` - Casual Leave
- `"sick"` - Sick Leave
- `"earned"` - Earned Leave
- `"unpaid"` - Unpaid Leave
- `"other"` - Other

## 📊 **Status Options**
- `"pending"` - Pending (default when created)
- `"approved"` - Approved by admin
- `"rejected"` - Rejected by admin

---

## 🔄 **API Workflow**

### Employee Workflow:
1. Employee creates leave request → **POST** `/api/leave/create/`
   - Status automatically set to `"pending"`
2. Employee can edit/delete if needed → **PATCH** `/api/leave/<id>/update/` or **DELETE** `/api/leave/<id>/delete/`
   - Only works for pending requests
3. Employee checks status → **GET** `/api/leave/list/` or `/api/leave/<id>/`
   - Can filter by status to see pending/approved/rejected requests
4. When admin approves/rejects, employee sees updated status in their list
   - Once approved/rejected, employee cannot edit/delete

### Admin Workflow:
1. Admin views all pending requests → **GET** `/api/leave/admin/list/?status=pending`
2. Admin reviews and makes decision → **PATCH** `/api/leave/admin/<id>/update/`
3. Status updated → Employee automatically sees the change in their mobile app

---

## 🚨 **Error Handling**

All APIs return appropriate HTTP status codes:
- **200 OK**: Success
- **201 Created**: Resource created successfully
- **400 Bad Request**: Validation errors
- **401 Unauthorized**: Missing or invalid token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

---

## 📝 **Example Mobile App Integration (Flutter/Dart)**

```dart
class LeaveRequestService {
  final String baseUrl = 'https://your-domain.com/employeeleave';
  final String token;
  
  LeaveRequestService(this.token);
  
  // Create Leave Request
  Future<Map<String, dynamic>> createLeaveRequest({
    required bool halfDay,
    required String leaveType,
    required String fromDate,
    required String toDate,
    required String email,
    String? reason,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/leave/create/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'half_day': halfDay,
        'leave_type': leaveType,
        'from_date': fromDate,
        'to_date': toDate,
        'email': email,
        'reason': reason ?? '',
      }),
    );
    return json.decode(response.body);
  }
  
  // Get User's Leave Requests
  Future<Map<String, dynamic>> getUserLeaveRequests({
    String? status,
    String? leaveType,
  }) async {
    String url = '$baseUrl/api/leave/list/';
    List<String> params = [];
    
    if (status != null) params.add('status=$status');
    if (leaveType != null) params.add('leave_type=$leaveType');
    
    if (params.isNotEmpty) {
      url += '?${params.join('&')}';
    }
    
    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  // Get Leave Request Detail
  Future<Map<String, dynamic>> getLeaveRequestDetail(int id) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/leave/$id/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  // Update Own Leave Request
  Future<Map<String, dynamic>> updateOwnLeaveRequest({
    required int id,
    bool? halfDay,
    String? leaveType,
    String? fromDate,
    String? toDate,
    String? email,
    String? reason,
  }) async {
    Map<String, dynamic> body = {};
    if (halfDay != null) body['half_day'] = halfDay;
    if (leaveType != null) body['leave_type'] = leaveType;
    if (fromDate != null) body['from_date'] = fromDate;
    if (toDate != null) body['to_date'] = toDate;
    if (email != null) body['email'] = email;
    if (reason != null) body['reason'] = reason;
    
    final response = await http.patch(
      Uri.parse('$baseUrl/api/leave/$id/update/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: json.encode(body),
    );
    return json.decode(response.body);
  }
  
  // Delete Own Leave Request
  Future<Map<String, dynamic>> deleteOwnLeaveRequest(int id) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/leave/$id/delete/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  // Admin: List All Leave Requests
  Future<Map<String, dynamic>> getAllLeaveRequests({
    String? status,
    String? leaveType,
    int? userId,
  }) async {
    String url = '$baseUrl/api/leave/admin/list/';
    List<String> params = [];
    
    if (status != null) params.add('status=$status');
    if (leaveType != null) params.add('leave_type=$leaveType');
    if (userId != null) params.add('user_id=$userId');
    
    if (params.isNotEmpty) {
      url += '?${params.join('&')}';
    }
    
    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  // Admin: Update Leave Status
  Future<Map<String, dynamic>> updateLeaveStatus({
    required int id,
    required String status,
    String? adminRemarks,
  }) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/api/leave/admin/$id/update/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'status': status,
        'admin_remarks': adminRemarks ?? '',
      }),
    );
    return json.decode(response.body);
  }
}
```

---

## ✅ **Quick Reference Summary**

### For Regular Employees:
1. **POST** `/employeeleave/api/leave/create/` - Create leave request
2. **GET** `/employeeleave/api/leave/list/` - View their leave requests
3. **GET** `/employeeleave/api/leave/<id>/` - View specific leave details
4. **PATCH/PUT** `/employeeleave/api/leave/<id>/update/` - Update own leave request (pending only)
5. **DELETE** `/employeeleave/api/leave/<id>/delete/` - Delete own leave request (pending only)

### For Admin Users:
1. **GET** `/employeeleave/api/leave/admin/list/` - View all leave requests
2. **PATCH** `/employeeleave/api/leave/admin/<id>/update/` - Approve/reject leave

---

All APIs are ready to use! 🚀

