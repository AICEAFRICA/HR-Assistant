# FastAPI Backend Setup and Usage Guide

## Overview
This document provides instructions for running and testing the FastAPI backend for the HR Assistant system.

## Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)
- All dependencies from requirements.txt

## Installation

### 1. Install FastAPI Dependencies
```bash
pip install fastapi uvicorn python-multipart pydantic
```

### 2. Update requirements.txt
```bash
# Add to your existing requirements.txt
fastapi>=0.95.0
uvicorn[standard]>=0.21.0
python-multipart>=0.0.5
pydantic>=1.10.0
```

### 3. Install all dependencies
```bash
pip install -r requirements.txt
```

## Running the API Server

### Option 1: Development Mode (with auto-reload)
```bash
cd "c:\Users\USER\Documents\HR agent Folder"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Expected Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Accessing the API

Once the server is running, you can access:

### 1. **Swagger UI (Interactive Documentation)**
```
http://localhost:8000/api/docs
```
This provides an interactive interface where you can:
- View all endpoints
- See request/response models
- Test endpoints directly
- View response examples

### 2. **ReDoc (Alternative Documentation)**
```
http://localhost:8000/api/redoc
```
Clean, readable documentation format

### 3. **Raw API**
```
http://localhost:8000/api/[endpoint]
```

### 4. **Root Endpoint**
```
http://localhost:8000/
```
Shows all available endpoints

## API Endpoints Overview

### System Endpoints
- `GET /api/health` - Health check
- `GET /` - API information

### RAG Query Endpoints
- `POST /api/query` - Submit HR question to RAG system
- `POST /api/query/router-info` - Get query routing information

### Leave Management
- `POST /api/leave/request` - Create leave request
- `GET /api/leave/employee/{email}` - Get employee's leave requests
- `GET /api/leave/all` - Get all leave requests (HR view)
- `PUT /api/leave/approve` - Approve/reject leave request
- `GET /api/leave/statistics` - Get leave statistics

### Employee Services - Insurance
- `POST /api/employee-services/insurance/enroll` - Enroll in insurance
- `GET /api/employee-services/insurance/{email}` - Get insurance records

### Employee Services - Shares
- `POST /api/employee-services/shares/allocate` - Allocate shares
- `GET /api/employee-services/shares/{email}` - Get share records

### Employee Services - Compliance
- `POST /api/employee-services/compliance/record` - Record training
- `GET /api/employee-services/compliance/{email}` - Get compliance status

### Employee Services - Governance
- `POST /api/employee-services/governance/role` - Create governance role
- `GET /api/employee-services/governance/structure` - Get organization structure

### Employee Services - Career Development
- `POST /api/employee-services/development/plan` - Create development plan
- `POST /api/employee-services/development/training` - Record training
- `GET /api/employee-services/development/{email}` - Get development profile

### Document Generation
- `POST /api/documents/generate` - Generate HR document
- `GET /api/documents/templates` - List available templates

### Dashboard
- `GET /api/dashboard/metrics` - Get dashboard metrics
- `GET /api/dashboard/analytics` - Get analytics data
- `GET /api/dashboard/summary` - Get complete summary

## Testing the API

### Option 1: Using Swagger UI
1. Navigate to http://localhost:8000/api/docs
2. Click on any endpoint to expand it
3. Click "Try it out" button
4. Fill in the required parameters
5. Click "Execute" to test

### Option 2: Using the Test Suite
```bash
python test_api.py
```

This will:
- Run 30+ automated tests against all endpoints
- Generate a test report: `api_test_results.json`
- Show pass/fail summary

### Option 3: Using cURL
```bash
# Health check
curl http://localhost:8000/api/health

# Submit a query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the company leave policy?",
    "is_urgent": false,
    "user_role": "Employee"
  }'
```

### Option 4: Using Python requests
```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "What is our attrition rate?",
        "is_urgent": True,
        "user_role": "HR Personnel"
    }
)
print(response.json())
```

## Example API Calls

### 1. Query the RAG System
```bash
POST /api/query
{
  "query": "How do I request vacation time?",
  "is_urgent": false,
  "user_role": "Employee"
}
```

### 2. Create a Leave Request
```bash
POST /api/leave/request
{
  "employee_name": "John Doe",
  "employee_email": "john.doe@example.com",
  "leave_type": "Annual Leave",
  "start_date": "2024-02-15",
  "end_date": "2024-02-22",
  "reason": "Planned vacation"
}
```

### 3. Enroll in Insurance
```bash
POST /api/employee-services/insurance/enroll
{
  "employee_email": "john.doe@example.com",
  "insurance_type": "Health",
  "coverage_amount": 50000,
  "effective_date": "2024-02-05",
  "beneficiary_name": "Jane Doe",
  "beneficiary_relation": "Spouse"
}
```

### 4. Generate Document
```bash
POST /api/documents/generate
{
  "document_type": "offer_letter",
  "template_data": {
    "employee_name": "John Doe",
    "position_title": "Senior Engineer",
    "department": "Engineering",
    "start_date": "2024-03-15",
    "salary": 120000,
    "employment_type": "Full-time",
    "response_deadline": "2024-02-12",
    "hr_manager_name": "Jane Smith",
    "company_name": "Adanian Labs"
  },
  "output_format": "html"
}
```

## API Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Service Status Check

To verify which services are initialized:
```bash
GET /api/health
```

Response example:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-05T10:30:45.123456",
  "services": {
    "query_router": true,
    "employee_services": true,
    "leave_service": true,
    "hr_dashboard": true,
    "document_generator": true
  }
}
```

## Troubleshooting

### 1. Port Already in Use
```bash
# Use a different port
uvicorn main:app --port 8001
```

### 2. Module Not Found
```bash
# Make sure you're in the correct directory
cd "c:\Users\USER\Documents\HR agent Folder"
```

### 3. Environment Variables Not Found
```bash
# Check that .env file exists with GEMINI_API_KEY
cat .env
```

### 4. Database Connection Issues
- Verify Supabase credentials in knowledge_base.py
- Check internet connection for API calls

## Development Notes

- The API uses FastAPI's automatic OpenAPI documentation
- All endpoints return appropriate HTTP status codes
- Request validation happens via Pydantic models
- CORS is enabled for all origins (can be restricted in production)
- Services are initialized on server startup

## Performance Tips

1. Use `/api/query` for intelligent routing (RAG or data)
2. Cache frequently accessed endpoints
3. Use query parameters for filtering
4. Monitor service health regularly

## Security Considerations (for production)

1. Restrict CORS origins
2. Add authentication middleware
3. Validate all inputs strictly
4. Use HTTPS in production
5. Implement rate limiting
6. Add request logging
7. Use API keys for sensitive endpoints

## Next Steps

1. Run the test suite: `python test_api.py`
2. Explore endpoints in Swagger UI: http://localhost:8000/api/docs
3. Integrate with frontend applications
4. Deploy to production (see deployment guide)

## Support

For issues or questions:
1. Check the API documentation at /api/docs
2. Review error messages in server logs
3. Check service initialization status at /api/health
4. Review test results in api_test_results.json
