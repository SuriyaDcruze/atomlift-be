# Mobile AMC API Documentation

This document describes the REST API endpoints for mobile app AMC (Annual Maintenance Contract) management. These APIs allow authenticated employees to view and create AMCs.

## Overview

The mobile AMC system provides APIs for employees to:
- View all AMCs with pagination and filtering
- Create new AMCs
- Access customer information linked to AMCs
- View AMC details including pricing and contract information

## Base URL
```
http://your-domain.com/amc/
```

## Authentication

All endpoints require authentication using the token received from the mobile authentication API:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## API Endpoints

### 1. List AMCs

**Endpoint**: `GET /amc/api/amc/list/`

**Description**: Retrieves all AMCs with pagination and filtering options.

**Query Parameters**:
- `q` (optional): Search term (searches in reference_id, amcname, customer site_name, equipment_no, latitude)
- `customer` (optional): Filter by customer ID
- `status` (optional): Filter by AMC status (`active`, `expired`, `cancelled`, `on_hold`)
- `amc_type` (optional): Filter by AMC type ID
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Number of items per page (default: None, shows all results)

**Example Request**:
```
GET /amc/api/amc/list/?status=active&page=1&page_size=20
```

**Response** (Success - 200):
```json
{
    "count": 45,
    "next": "http://your-domain.com/amc/api/amc/list/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "reference_id": "AMC01",
            "amcname": "Annual Maintenance Contract - ABC Building",
            "latitude": "123 Main Street, City",
            "equipment_no": "EQ001",
            "invoice_frequency": "annually",
            "invoice_frequency_display": "Annually",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "notes": "Regular maintenance contract for lift system",
            "is_generate_contract": true,
            "no_of_services": 12,
            "price": "15000.00",
            "no_of_lifts": 2,
            "gst_percentage": "18.00",
            "total": "35400.00",
            "contract_amount": "35400.00",
            "total_amount_paid": "10000.00",
            "amount_due": "25400.00",
            "status": "active",
            "status_display": "Active",
            "created": "2024-01-01T10:00:00Z",
            "customer_name": "ABC Building",
            "customer_site_address": "123 Main Street, City",
            "customer_job_no": "JOB001",
            "customer_email": "contact@abcbuilding.com",
            "customer_phone": "+1234567890",
            "amc_type_name": "Comprehensive",
            "payment_terms_name": "Monthly"
        },
        {
            "id": 2,
            "reference_id": "AMC02",
            "amcname": "Basic Maintenance - XYZ Complex",
            "latitude": "456 Park Avenue, City",
            "equipment_no": "EQ002",
            "invoice_frequency": "quarterly",
            "invoice_frequency_display": "Quarterly",
            "start_date": "2024-03-01",
            "end_date": "2025-03-01",
            "notes": "Quarterly maintenance service",
            "is_generate_contract": true,
            "no_of_services": 4,
            "price": "5000.00",
            "no_of_lifts": 1,
            "gst_percentage": "18.00",
            "total": "5900.00",
            "contract_amount": "5900.00",
            "total_amount_paid": "5900.00",
            "amount_due": "0.00",
            "status": "active",
            "status_display": "Active",
            "created": "2024-03-01T09:00:00Z",
            "customer_name": "XYZ Complex",
            "customer_site_address": "456 Park Avenue, City",
            "customer_job_no": "JOB002",
            "customer_email": "info@xyzcomplex.com",
            "customer_phone": "+1234567891",
            "amc_type_name": "Basic",
            "payment_terms_name": "Quarterly"
        }
    ]
}
```

### 2. Create AMC

**Endpoint**: `POST /amc/api/amc/create/`

**Description**: Creates a new AMC record.

**Request Body**:
```json
{
    "customer": 1,
    "amcname": "Annual Maintenance Contract - New Building",
    "latitude": "789 High Street, City",
    "equipment_no": "EQ003",
    "invoice_frequency": "annually",
    "amc_type": 1,
    "payment_terms": 1,
    "start_date": "2024-04-01",
    "end_date": "2025-04-01",
    "notes": "New maintenance contract",
    "is_generate_contract": true,
    "no_of_services": 12,
    "price": "20000.00",
    "no_of_lifts": 3,
    "gst_percentage": "18.00",
    "amc_service_item": 1
}
```

**Required Fields**:
- `customer`: Customer ID (integer)
- `start_date`: Start date (YYYY-MM-DD format)

**Optional Fields**:
- `amcname`: Name of the AMC
- `latitude`: Site address
- `equipment_no`: Equipment number
- `invoice_frequency`: Frequency of invoicing (`annually`, `semi_annually`, `quarterly`, `monthly`, `per_service`)
- `amc_type`: AMC type ID
- `payment_terms`: Payment terms ID
- `end_date`: End date (YYYY-MM-DD format, auto-calculated as +1 year from start_date if not provided)
- `notes`: Additional notes
- `is_generate_contract`: Whether to generate contract (boolean)
- `no_of_services`: Number of services
- `price`: Price per lift
- `no_of_lifts`: Number of lifts
- `gst_percentage`: GST percentage
- `amc_service_item`: Service item ID

**Response** (Success - 201):
```json
{
    "message": "AMC created successfully",
    "amc": {
        "id": 3,
        "reference_id": "AMC03",
        "amcname": "Annual Maintenance Contract - New Building",
        "customer": "New Building",
        "start_date": "2024-04-01",
        "end_date": "2025-04-01",
        "status": "active"
    }
}
```

### 3. List AMC Types

**Endpoint**: `GET /amc/api/amc/types/list/`

**Description**: Retrieves all available AMC types for mobile app.

**Response** (Success - 200):
```json
{
    "amc_types": [
        {
            "id": 1,
            "name": "Comprehensive"
        },
        {
            "id": 2,
            "name": "Basic"
        },
        {
            "id": 3,
            "name": "Premium"
        }
    ]
}
```

### 3b. Create AMC Type

**Endpoint**: `POST /amc/api/amc/types/create/`

**Description**: Creates a new AMC type from mobile app.

**Request Body**:
```json
{
    "name": "Extended Warranty"
}
```

**Required Fields**:
- `name`: Name of the AMC type (string)

**Response** (Success - 201):
```json
{
    "message": "AMC type created successfully",
    "amc_type": {
        "id": 4,
        "name": "Extended Warranty"
    }
}
```

**Note**: AMC types created via mobile app will automatically appear in the Wagtail admin panel under "AMC Types".

### 4. List Payment Terms

**Endpoint**: `GET /amc/api/amc/payment-terms/`

**Description**: Retrieves all available payment terms.

**Response** (Success - 200):
```json
[
    {
        "id": 1,
        "name": "Monthly"
    },
    {
        "id": 2,
        "name": "Quarterly"
    },
    {
        "id": 3,
        "name": "Annually"
    }
]
```

### 5. Get Next AMC Reference

**Endpoint**: `GET /amc/api/amc/next-reference/`

**Description**: Returns the next available AMC reference ID.

**Response** (Success - 200):
```json
{
    "reference_id": "AMC04"
}
```

## Error Responses

### 400 Bad Request (Validation Error)
```json
{
    "customer": ["This field is required."],
    "start_date": ["This field is required."]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "Access denied. Only employees can view AMCs."
}
```

### 500 Internal Server Error
```json
{
    "error": "An error occurred while processing your request."
}
```

## Usage Examples

### JavaScript/React Native Example

```javascript
// List AMCs
const listAMCs = async (token, filters = {}) => {
    const queryParams = new URLSearchParams(filters);
    const response = await fetch(`http://your-domain.com/amc/api/amc/list/?${queryParams}`, {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Create AMC
const createAMC = async (token, amcData) => {
    const response = await fetch('http://your-domain.com/amc/api/amc/create/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(amcData)
    });
    return await response.json();
};

// Get AMC types
const getAMCTypes = async (token) => {
    const response = await fetch('http://your-domain.com/amc/api/amc/types/list/', {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Create AMC type
const createAMCType = async (token, name) => {
    const response = await fetch('http://your-domain.com/amc/api/amc/types/create/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name })
    });
    return await response.json();
};

// Get payment terms
const getPaymentTerms = async (token) => {
    const response = await fetch('http://your-domain.com/amc/api/amc/payment-terms/', {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Get next reference
const getNextReference = async (token) => {
    const response = await fetch('http://your-domain.com/amc/api/amc/next-reference/', {
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    });
    return await response.json();
};

// Usage examples
const amcs = await listAMCs(token, { status: 'active', page: 1, page_size: 20 });

const newAMC = await createAMC(token, {
    customer: 1,
    amcname: "New AMC Contract",
    latitude: "123 Street",
    equipment_no: "EQ001",
    invoice_frequency: "annually",
    start_date: "2024-04-01",
    is_generate_contract: true,
    no_of_services: 12,
    price: "15000.00",
    no_of_lifts: 2,
    gst_percentage: "18.00"
});

const amcTypes = await getAMCTypes(token);
const newAMCType = await createAMCType(token, 'Extended Warranty');
const paymentTerms = await getPaymentTerms(token);
const nextRef = await getNextReference(token);
```

### Flutter/Dart Example

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class AMCService {
  static const String baseUrl = 'http://your-domain.com/amc';
  
  static Future<Map<String, dynamic>> listAMCs(String token, {Map<String, String>? filters}) async {
    String queryParams = '';
    if (filters != null && filters.isNotEmpty) {
      queryParams = '?' + filters.entries.map((e) => '${e.key}=${e.value}').join('&');
    }
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/amc/list/$queryParams'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> createAMC(String token, Map<String, dynamic> amcData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/amc/create/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: json.encode(amcData),
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> getAMCTypes(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/amc/types/list/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> createAMCType(String token, String name) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/amc/types/create/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: json.encode({'name': name}),
    );
    return json.decode(response.body);
  }
  
  static Future<List<dynamic>> getPaymentTerms(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/amc/payment-terms/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
  
  static Future<Map<String, dynamic>> getNextReference(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/amc/next-reference/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return json.decode(response.body);
  }
}

// Usage example
void main() async {
  String token = '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b';
  
  // List active AMCs
  var amcs = await AMCService.listAMCs(token, {
    'status': 'active',
    'page': '1',
    'page_size': '20'
  });
  print('Total AMCs: ${amcs['count']}');
  
  // Create new AMC
  var newAMC = await AMCService.createAMC(token, {
    'customer': 1,
    'amcname': 'New Contract',
    'latitude': '123 Street',
    'equipment_no': 'EQ001',
    'invoice_frequency': 'annually',
    'start_date': '2024-04-01',
    'is_generate_contract': true,
    'no_of_services': 12,
    'price': '15000.00',
    'no_of_lifts': 2,
    'gst_percentage': '18.00'
  });
  print('Created AMC: ${newAMC['amc']['reference_id']}');
  
  // Get dropdown options
  var amcTypes = await AMCService.getAMCTypes(token);
  var newAMCType = await AMCService.createAMCType(token, 'Extended Warranty');
  var paymentTerms = await AMCService.getPaymentTerms(token);
  var nextRef = await AMCService.getNextReference(token);
  print('Next reference: ${nextRef['reference_id']}');
}
```

## Automatic Calculations

When creating or updating an AMC, the following fields are automatically calculated:

1. **Reference ID**: Auto-generated as `AMC01`, `AMC02`, etc.
2. **End Date**: If not provided, automatically set to +1 year from start_date
3. **Total**: Calculated as `price * no_of_lifts * (1 + gst_percentage/100)`
4. **Contract Amount**: Same as total
5. **Amount Due**: Calculated as `contract_amount - total_amount_paid`
6. **Status**: Automatically determined based on dates:
   - `active`: If current date is between start_date and end_date
   - `expired`: If current date is after end_date
   - `on_hold`: If current date is before start_date
   - `cancelled`: Manual setting required

## Status Options

- `active`: AMC is currently active
- `expired`: AMC has expired
- `cancelled`: AMC was cancelled
- `on_hold`: AMC is scheduled to start in the future

## Invoice Frequency Options

- `annually`: Invoice once per year
- `semi_annually`: Invoice twice per year
- `quarterly`: Invoice four times per year
- `monthly`: Invoice twelve times per year
- `per_service`: Invoice after each service

## Security Features

1. **Token Authentication**: All endpoints require valid authentication token
2. **Employee Group Restriction**: Only users in employee groups can access these APIs
3. **Input Validation**: All input data is validated before processing
4. **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
5. **Auto-calculation**: Total, contract amount, and due amount are automatically calculated to prevent errors

## Notes

1. **Pagination**: List endpoint supports pagination for better performance
2. **Filtering**: AMCs can be filtered by status, customer, and AMC type
3. **Search**: Full-text search across multiple fields
4. **Customer Information**: List endpoint includes customer details (name, address, contact info)
5. **Auto Status**: AMC status is automatically calculated based on dates
6. **Contract Generation**: Set `is_generate_contract` to true to automatically calculate contract amounts

