# Business Hours API - Postman Examples

This document provides Postman examples for the Business Hours API endpoints.

## Base URL
- **Development**: `http://localhost:8000` or `http://127.0.0.1:8000`
- **Production**: `https://app.fixcars.ro` or `https://www.app.fixcars.ro`

## Authentication
Both endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

To get an access token, first login using the `/api/login/` endpoint.

---

## Endpoint 1: Get Business Hours

**GET** `/api/business-hours/`

Fetches the business hours for the currently authenticated user (must be a supplier).

### Postman Configuration

**Method**: `GET`

**URL**: 
```
http://localhost:8000/api/business-hours/
```
or
```
https://app.fixcars.ro/api/business-hours/
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM1ODk2NDAwLCJpYXQiOjE3MzQ5MzI0MDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ.example_token_here
Content-Type: application/json
```

**Body**: None (GET request)

### Example Response (Success - 200 OK)

```json
{
    "success": true,
    "data": {
        "monday": {
            "open": "08:00",
            "close": "19:00",
            "closed": false
        },
        "tuesday": {
            "open": "08:00",
            "close": "19:00",
            "closed": false
        },
        "wednesday": {
            "open": "08:00",
            "close": "19:00",
            "closed": false
        },
        "thursday": {
            "open": "08:00",
            "close": "19:00",
            "closed": false
        },
        "friday": {
            "open": "08:00",
            "close": "19:00",
            "closed": false
        },
        "saturday": {
            "open": "09:00",
            "close": "17:00",
            "closed": true
        },
        "sunday": {
            "open": "09:00",
            "close": "17:00",
            "closed": true
        }
    }
}
```

### Example Response (Error - 403 Forbidden)

```json
{
    "success": false,
    "error": "Business hours are only available for suppliers."
}
```

### Example Response (Error - 401 Unauthorized)

```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## Endpoint 2: Update Business Hours

**PUT** `/api/business-hours/update/`

Updates the business hours for the currently authenticated user (must be a supplier).

### Postman Configuration

**Method**: `PUT`

**URL**: 
```
http://localhost:8000/api/business-hours/update/
```
or
```
https://app.fixcars.ro/api/business-hours/update/
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM1ODk2NDAwLCJpYXQiOjE3MzQ5MzI0MDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ.example_token_here
Content-Type: application/json
```

**Body** (raw JSON):

```json
{
    "monday": {
        "open": "09:00",
        "close": "18:00",
        "closed": false
    },
    "tuesday": {
        "open": "09:00",
        "close": "18:00",
        "closed": false
    },
    "wednesday": {
        "open": "09:00",
        "close": "18:00",
        "closed": false
    },
    "thursday": {
        "open": "09:00",
        "close": "18:00",
        "closed": false
    },
    "friday": {
        "open": "09:00",
        "close": "18:00",
        "closed": false
    },
    "saturday": {
        "open": "10:00",
        "close": "16:00",
        "closed": false
    },
    "sunday": {
        "open": "10:00",
        "close": "16:00",
        "closed": true
    }
}
```

### Important Notes:
- **Time Format**: All times must be in **24-hour format** (HH:MM)
  - Valid examples: `"08:00"`, `"09:30"`, `"17:45"`, `"23:59"`
  - Invalid examples: `"8:00"` (missing leading zero), `"9:30 AM"` (12-hour format), `"25:00"` (invalid hour)
- **All days are optional**: You can update only specific days if needed
- **Each day object requires**:
  - `open`: String in HH:MM format (24-hour system)
  - `close`: String in HH:MM format (24-hour system)
  - `closed`: Boolean (true if the business is closed that day)

### Example Response (Success - 200 OK)

```json
{
    "success": true,
    "message": "Business hours updated successfully.",
    "data": {
        "monday": {
            "open": "09:00",
            "close": "18:00",
            "closed": false
        },
        "tuesday": {
            "open": "09:00",
            "close": "18:00",
            "closed": false
        },
        "wednesday": {
            "open": "09:00",
            "close": "18:00",
            "closed": false
        },
        "thursday": {
            "open": "09:00",
            "close": "18:00",
            "closed": false
        },
        "friday": {
            "open": "09:00",
            "close": "18:00",
            "closed": false
        },
        "saturday": {
            "open": "10:00",
            "close": "16:00",
            "closed": false
        },
        "sunday": {
            "open": "10:00",
            "close": "16:00",
            "closed": true
        }
    }
}
```

### Example Response (Error - 400 Bad Request)

```json
{
    "success": false,
    "errors": {
        "monday": {
            "open": [
                "monday.open must be in HH:MM format (24-hour system)"
            ]
        }
    }
}
```

### Example Response (Error - 403 Forbidden)

```json
{
    "success": false,
    "error": "Business hours can only be updated by suppliers."
}
```

### Example Response (Error - 401 Unauthorized)

```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## Complete Example: Updating Only Specific Days

You can update only specific days. Days not included in the request will remain unchanged:

**Body** (raw JSON):

```json
{
    "saturday": {
        "open": "10:00",
        "close": "16:00",
        "closed": false
    },
    "sunday": {
        "open": "10:00",
        "close": "16:00",
        "closed": true
    }
}
```

This will only update Saturday and Sunday, leaving Monday through Friday unchanged.

---

## Postman Collection Setup

### Step 1: Create Environment Variables

In Postman, create an environment with these variables:
- `base_url`: `http://localhost:8000` (or your production URL)
- `access_token`: Your JWT access token (obtained from login)

### Step 2: Configure Requests

**Get Business Hours Request**:
- Method: `GET`
- URL: `{{base_url}}/api/business-hours/`
- Headers:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`

**Update Business Hours Request**:
- Method: `PUT`
- URL: `{{base_url}}/api/business-hours/update/`
- Headers:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- Body: Select "raw" and "JSON", then paste the JSON body from the example above

### Step 3: Get Access Token First

Before testing these endpoints, you need to login:

**Login Request**:
- Method: `POST`
- URL: `{{base_url}}/api/login/`
- Body (raw JSON):
```json
{
    "email": "supplier@example.com",
    "password": "your_password"
}
```

- Response will include `access_token` - copy this to your environment variable.

---

## Testing Checklist

- [ ] Login and obtain access token
- [ ] Set access token in environment variable
- [ ] Test GET `/api/business-hours/` - should return current business hours
- [ ] Test PUT `/api/business-hours/update/` with valid data - should update successfully
- [ ] Test PUT with invalid time format (e.g., "8:00" instead of "08:00") - should return validation error
- [ ] Test PUT with missing required fields - should return validation error
- [ ] Test with non-supplier account - should return 403 Forbidden
- [ ] Test without authentication - should return 401 Unauthorized

