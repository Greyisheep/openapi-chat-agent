# Postman Debug Guide

## Issue: Request body being sent as string instead of JSON

The error you're seeing suggests that Postman is sending the request body as a string instead of proper JSON.

## Debug Steps:

### 1. Check Environment Variables
Make sure you've imported the environment file:
- File: `OpenAPI_Chat_Agent_Environment.postman_environment.json`
- In Postman: Go to Settings (gear icon) → Import → Select the environment file

### 2. Verify Environment is Active
- In Postman, check the environment dropdown (top right)
- Make sure "OpenAPI Chat Agent - Local Development" is selected

### 3. Test Environment Variables
Create a simple test request to verify variables are working:
- Method: GET
- URL: `{{base_url}}/health/`
- This should resolve to: `http://localhost:8000/health/`

### 4. Manual Test (Alternative)
If the environment variables aren't working, try the request with hardcoded values:

```json
{
  "email": "greyisheep@gmail.com",
  "username": "Greyisheep", 
  "password": "SecurePass123!",
  "full_name": "Grey Sheep"
}
```

### 5. Check Request Headers
Make sure the request has:
- `Content-Type: application/json`

### 6. Disable Pre-request Script Temporarily
If the issue persists, try disabling the pre-request script:
- Edit the collection
- Go to the "Pre-request Scripts" tab
- Comment out or remove the script temporarily

### 7. Alternative: Use Raw JSON
Instead of using environment variables, try hardcoding the values in the request body to isolate the issue.

## Working curl command for reference:
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "greyisheep@gmail.com", "username": "Greyisheep", "password": "SecurePass123!", "full_name": "Grey Sheep"}'
```

## Expected Response:
```json
{
  "id": "fdf3cf9b-9872-4bd0-96c3-6cfd9eb2d445",
  "email": "greyisheep@gmail.com",
  "username": "Greyisheep",
  "full_name": "Grey Sheep",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-08-24T18:30:19.327405Z",
  "last_login": null
}
```
