# SIMPLIFIED Mobile Complaints API Documentation

## 🎯 **Only 3 API Endpoints Needed!**

I've consolidated all mobile complaints functionality into just **3 simple endpoints** that cover everything your React Native app needs.

---

## 📋 **Complete API List**

### **Authentication APIs** (4 endpoints)
```
POST /auth/api/mobile/generate-otp/          # Send OTP to email
POST /auth/api/mobile/verify-otp/            # Verify OTP & login
GET  /auth/api/mobile/user-details/          # Get user profile
POST /auth/api/mobile/logout/                # Logout
```

### **Complaints APIs** (3 endpoints)
```
GET  /complaints/api/mobile/complaints/                    # Get complaints + reference data
GET  /complaints/api/mobile/complaints/{reference}/        # Get complaint details
POST /complaints/api/mobile/complaints/{reference}/update/ # Update everything
```

---

## 🔐 **Authentication APIs**

### 1. Generate OTP
```
POST /auth/api/mobile/generate-otp/
```
**Request:**
```json
{
    "email": "user@example.com"
}
```
**Response:**
```json
{
    "message": "OTP sent successfully to your email",
    "otp_type": "email",
    "contact_info": "user@example.com",
    "expires_in_minutes": 10
}
```

### 2. Verify OTP & Login
```
POST /auth/api/mobile/verify-otp/
```
**Request:**
```json
{
    "email": "user@example.com",
    "otp_code": "123456"
}
```
**Response:**
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "profile": {
            "branch": "Main Branch",
            "designation": "Manager"
        }
    },
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "message": "Login successful"
}
```

### 3. Get User Details
```
GET /auth/api/mobile/user-details/
```
**Headers:** `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

### 4. Logout
```
POST /auth/api/mobile/logout/
```
**Headers:** `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

---

## 📱 **Complaints APIs**

### 1. Get Complaints List + Reference Data
```
GET /complaints/api/mobile/complaints/
```
**Headers:** `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

**Query Parameters:**
- `status` (optional): `open`, `in_progress`, `closed`
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response:**
```json
{
    "complaints": [
        {
            "id": 1,
            "reference": "CMP1001",
            "complaint_type": {"id": 1, "name": "Lift Not Working"},
            "customer": {
                "site_name": "ABC Building",
                "contact_person_name": "John Doe",
                "phone": "+1234567890"
            },
            "status": "open",
            "priority": {"id": 1, "name": "High"},
            "subject": "Lift Not Working",
            "technician_remark": "",
            "solution": "",
            "technician_signature_url": null,
            "customer_signature_url": null,
            "days_since_created": 0
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 3,
        "total_count": 45,
        "has_next": true
    },
    "reference_data": {
        "complaint_types": [
            {"id": 1, "name": "Lift Not Working"},
            {"id": 2, "name": "Door Not Opening"}
        ],
        "priorities": [
            {"id": 1, "name": "High"},
            {"id": 2, "name": "Medium"},
            {"id": 3, "name": "Low"}
        ]
    },
    "message": "Complaints retrieved successfully"
}
```

### 2. Get Complaint Details
```
GET /complaints/api/mobile/complaints/{reference}/
```
**Example:** `GET /complaints/api/mobile/complaints/CMP1001/`

**Response:**
```json
{
    "complaint": {
        "id": 1,
        "reference": "CMP1001",
        "complaint_type": {"id": 1, "name": "Lift Not Working"},
        "customer": {
            "site_name": "ABC Building",
            "contact_person_name": "John Doe",
            "phone": "+1234567890",
            "site_address": "123 Main Street"
        },
        "status": "open",
        "priority": {"id": 1, "name": "High"},
        "subject": "Lift Not Working",
        "message": "Lift is not responding to calls",
        "technician_remark": "",
        "solution": "",
        "technician_signature_url": null,
        "customer_signature_url": null,
        "assignment_history": [
            {
                "assigned_to_name": "John Technician",
                "assigned_by_name": "Admin User",
                "assignment_date": "2024-01-15T10:30:00Z",
                "message": "Please resolve this complaint"
            }
        ],
        "status_history": [
            {
                "old_status": "open",
                "new_status": "in_progress",
                "changed_by_name": "John Technician",
                "change_reason": "Started working on the complaint",
                "changed_at": "2024-01-15T11:00:00Z",
                "changed_from_mobile": true
            }
        ]
    },
    "message": "Complaint details retrieved successfully"
}
```

### 3. Update Complaint (Everything in One Request!)
```
POST /complaints/api/mobile/complaints/{reference}/update/
```
**Headers:** `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

**Request Body** (application/json):
```json
{
    "status": "closed",
    "technician_remark": "Completed repair work",
    "solution": "Lift is now working properly",
    "technician_signature": "John Technician",
    "customer_signature": "Jane Customer",
    "change_reason": "Work completed successfully"
}
```

**Response:**
```json
{
    "complaint": {
        "id": 1,
        "reference": "CMP1001",
        "status": "closed",
        "technician_remark": "Completed repair work",
        "solution": "Lift is now working properly",
        "technician_signature": "John Technician",
        "customer_signature": "Jane Customer",
        "status_history": [
            {
                "old_status": "in_progress",
                "new_status": "closed",
                "changed_by_name": "John Technician",
                "change_reason": "Work completed successfully",
                "changed_at": "2024-01-15T14:30:00Z",
                "changed_from_mobile": true
            }
        ]
    },
    "message": "Complaint updated successfully"
}
```

---

## 📱 **Complete React Native Integration**

```javascript
// API Configuration
const API_BASE_URL = 'http://your-domain.com';
const AUTH_TOKEN_KEY = 'auth_token';

// Authentication APIs
export const authAPI = {
    generateOTP: async (email) => {
        const response = await fetch(`${API_BASE_URL}/auth/api/mobile/generate-otp/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        return await response.json();
    },

    verifyOTP: async (email, otpCode) => {
        const response = await fetch(`${API_BASE_URL}/auth/api/mobile/verify-otp/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, otp_code: otpCode })
        });
        return await response.json();
    },

    getUserDetails: async (token) => {
        const response = await fetch(`${API_BASE_URL}/auth/api/mobile/user-details/`, {
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    },

    logout: async (token) => {
        const response = await fetch(`${API_BASE_URL}/auth/api/mobile/logout/`, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    }
};

// Complaints APIs
export const complaintsAPI = {
    // Get complaints list with reference data
    getComplaints: async (token, filters = {}) => {
        const queryParams = new URLSearchParams(filters);
        const response = await fetch(`${API_BASE_URL}/complaints/api/mobile/complaints/?${queryParams}`, {
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    },

    // Get complaint details
    getComplaintDetail: async (token, reference) => {
        const response = await fetch(`${API_BASE_URL}/complaints/api/mobile/complaints/${reference}/`, {
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    },

    // Update complaint with everything
    updateComplaint: async (token, reference, updateData) => {
        const response = await fetch(`${API_BASE_URL}/complaints/api/mobile/complaints/${reference}/update/`, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        return await response.json();
    }
};

// Complete Usage Example
const completeWorkflow = async () => {
    try {
        // Step 1: Login
        const otpResponse = await authAPI.generateOTP('user@example.com');
        const loginResponse = await authAPI.verifyOTP('user@example.com', '123456');
        const token = loginResponse.token;

        // Step 2: Get complaints with reference data
        const complaintsData = await complaintsAPI.getComplaints(token);
        console.log('Complaints:', complaintsData.complaints.length);
        console.log('Complaint Types:', complaintsData.reference_data.complaint_types);
        console.log('Priorities:', complaintsData.reference_data.priorities);

        // Step 3: Get specific complaint details
        const complaintDetail = await complaintsAPI.getComplaintDetail(token, 'CMP1001');
        console.log('Complaint Details:', complaintDetail.complaint.subject);

        // Step 4: Update complaint with signatures
        const updateResult = await complaintsAPI.updateComplaint(token, 'CMP1001', {
            status: 'closed',
            technician_remark: 'Repair completed successfully',
            solution: 'Replaced faulty component',
            technician_signature: 'John Technician',
            customer_signature: 'Jane Customer',
            change_reason: 'Work completed and customer satisfied'
        });
        
        console.log('Update Result:', updateResult.message);
        console.log('Technician Signature:', updateResult.complaint.technician_signature);
        console.log('Customer Signature:', updateResult.complaint.customer_signature);

        return { success: true, data: updateResult };
    } catch (error) {
        console.error('Error:', error);
        return { success: false, error: error.message };
    }
};
```

---

## 🎯 **Key Benefits of Simplified APIs**

### ✅ **Only 7 Total Endpoints**
- **4 Authentication APIs** (login, logout, user details)
- **3 Complaints APIs** (list, details, update)

### ✅ **Consolidated Functionality**
- **One endpoint** gets complaints + reference data (types, priorities)
- **One endpoint** handles all updates (status, remarks, solutions, signatures)
- **No separate API calls** needed for different functions

### ✅ **Real-time Admin Updates**
- All changes automatically appear in Wagtail admin
- Complete audit trail with timestamps
- Status change history tracking

### ✅ **Complete Feature Set**
- ✅ Authentication with OTP
- ✅ Complaints list with pagination & filtering
- ✅ Complaint details with full history
- ✅ Status updates with reasons
- ✅ Technician remarks
- ✅ Solutions
- ✅ Technician signatures (text)
- ✅ Customer signatures (text)
- ✅ Real-time admin visibility

---

## 🔒 **Security Features**

- **Token Authentication**: All endpoints require valid token
- **Employee Group Restriction**: Only employees can access
- **Assignment Validation**: Users can only access their assigned complaints
- **Text Validation**: Signature text fields validated for length
- **Complete Audit Trail**: All changes tracked with timestamps

---

## 📊 **Base URL**
```
http://your-domain.com
```

## 🔑 **Authentication Header**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

Your React Native app now needs only **7 simple API endpoints** to handle complete complaint management with text signatures, remarks, solutions, and real-time admin updates!
