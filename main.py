# -*- coding: utf-8 -*-
"""
FastAPI Backend for HR Assistant System
Comprehensive API with all services integrated
"""
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import date, datetime
import os
import logging
from uuid import UUID

from query_router import HRQueryRouter
from employee_services import EmployeeServicesManager
from leave_management import LeaveManagementService
from hr_analytics import HRAnalyticsService
from performance_analytics import PerformanceAnalyticsService
from document_generator import DocumentGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HR Assistant API",
    description="Comprehensive HR Management System API with RAG, Employee Services, Leave Management, and Document Generation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PYDANTIC MODELS ====================

# Query Models
class QueryRequest(BaseModel):
    """Model for RAG query requests"""
    query: str = Field(..., description="HR question or query")
    is_urgent: bool = Field(False, description="Mark as urgent query")
    user_role: str = Field("Employee", description="User role: Employee or HR Personnel")
    
class QueryResponse(BaseModel):
    """Model for RAG query responses"""
    answer: str
    confidence_score: float
    confidence_level: str
    query_type: str
    data_type: str
    response_type: str
    sources_used: int
    chunks: List[Dict] = []
    coverage: str

# Leave Models
class LeaveRequestCreate(BaseModel):
    """Model for creating leave requests"""
    employee_name: str = Field(..., description="Employee full name")
    employee_email: str = Field(..., description="Employee email address")
    leave_type: str = Field(..., description="Type of leave: Annual, Sick, Personal, etc.")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date")
    reason: str = Field(..., description="Reason for leave")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")

class LeaveRequest(LeaveRequestCreate):
    """Leave request response model"""
    id: int
    status: str
    request_date: datetime

class LeaveApprovalRequest(BaseModel):
    """Model for approving/rejecting leave requests"""
    request_id: str = Field(..., description="Leave request ID (UUID)")
    status: str = Field(..., description="Approval status: approved or rejected")
    hr_comments: str = Field(..., description="HR reviewer comments")
    hr_reviewer: str = Field(..., description="HR personnel name")

# Insurance Models
class InsuranceEnrollment(BaseModel):
    """Model for insurance enrollment"""
    employee_email: str = Field(..., description="Employee email")
    insurance_type: str = Field(..., description="Insurance type: Health, Life, Dental, Vision")
    coverage_amount: float = Field(..., description="Coverage amount in USD")
    effective_date: date = Field(..., description="Effective date")
    beneficiary_name: Optional[str] = Field(None, description="Beneficiary name")
    beneficiary_relation: Optional[str] = Field(None, description="Relationship to employee")

class InsuranceRecord(InsuranceEnrollment):
    """Insurance record response"""
    id: int
    status: str
    enrollment_date: datetime

# Shares Models
class ShareAllocation(BaseModel):
    """Model for share allocation"""
    employee_email: str = Field(..., description="Employee email")
    shares_count: int = Field(..., description="Number of shares")
    share_price: float = Field(..., description="Share price in USD")
    grant_date: date = Field(..., description="Grant date")
    vesting_period_months: int = Field(..., description="Vesting period in months")

class ShareRecord(ShareAllocation):
    """Share allocation response"""
    id: int
    vested_shares: int
    total_value: float

# Compliance Models
class ComplianceTraining(BaseModel):
    """Model for compliance training"""
    employee_email: str = Field(..., description="Employee email")
    training_type: str = Field(..., description="Training type: GDPR, HIPAA, Anti-Corruption, etc.")
    completion_date: date = Field(..., description="Completion date")
    expiry_date: date = Field(..., description="Expiry date")
    certificate_url: Optional[str] = Field(None, description="Certificate URL")

class ComplianceRecord(ComplianceTraining):
    """Compliance training response"""
    id: int
    status: str

# Governance Models
class GovernanceRole(BaseModel):
    """Model for governance role"""
    role_name: str = Field(..., description="Role name")
    department: str = Field(..., description="Department")
    responsibilities: List[str] = Field(..., description="List of responsibilities")
    reporting_to: Optional[str] = Field(None, description="Reports to")

# Career Development Models
class DevelopmentPlan(BaseModel):
    """Model for development plan"""
    employee_email: str = Field(..., description="Employee email")
    plan_title: str = Field(..., description="Plan title")
    goals: List[Dict] = Field(..., description="Development goals")
    timeline_months: int = Field(..., description="Timeline in months")
    mentor_email: Optional[str] = Field(None, description="Mentor email")

class TrainingCompletion(BaseModel):
    """Model for training completion"""
    employee_email: str = Field(..., description="Employee email")
    training_name: str = Field(..., description="Training name")
    training_date: date = Field(..., description="Training date")
    provider: str = Field(..., description="Training provider")
    certificate_url: Optional[str] = Field(None, description="Certificate URL")

# Document Generation Models
class DocumentGenerationPayload(BaseModel):
    """Single unified document generation request"""
    document_type: str = Field(..., description="offer_letter, termination_letter, or experience_certificate")
    template_data: Dict[str, Any] = Field(..., description="Form fields for the selected document type")
    output_format: str = Field("html", description="html, docx, or pdf")

# Specific models for each document type - These show exact required fields in Swagger
class OfferLetterRequest(BaseModel):
    """Offer Letter - Fill all fields and submit"""
    document_type: str = Field("offer_letter", description="Document type")
    employee_name: str = Field(..., description="Employee full name")
    position_title: str = Field(..., description="Job position title")
    department: str = Field(..., description="Department name")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    salary: float = Field(..., description="Annual salary")
    employment_type: str = Field(..., description="Full-time, Part-time, or Contract")
    response_deadline: str = Field(..., description="Deadline (YYYY-MM-DD)")
    hr_manager_name: str = Field(..., description="HR manager name")
    company_name: str = Field(..., description="Company name")
    output_format: str = Field("html", description="html, docx, or pdf")

class TerminationLetterRequest(BaseModel):
    """Termination Letter - Fill all fields and submit"""
    document_type: str = Field("termination_letter", description="Document type")
    employee_name: str = Field(..., description="Employee full name")
    employee_id: str = Field(..., description="Employee ID")
    position_title: str = Field(..., description="Job position title")
    department: str = Field(..., description="Department name")
    termination_date: str = Field(..., description="Termination date (YYYY-MM-DD)")
    last_working_day: str = Field(..., description="Last working day (YYYY-MM-DD)")
    termination_reason: str = Field(..., description="Reason for termination")
    hr_manager_name: str = Field(..., description="HR manager name")
    company_name: str = Field(..., description="Company name")
    final_salary: Optional[float] = Field(None, description="Final salary (optional)")
    unused_leave_days: Optional[int] = Field(None, description="Unused leave days (optional)")
    unused_leave_amount: Optional[float] = Field(None, description="Leave amount (optional)")
    total_settlement: Optional[float] = Field(None, description="Total settlement (optional)")
    output_format: str = Field("html", description="html, docx, or pdf")

class ExperienceCertificateRequest(BaseModel):
    """Experience Certificate - Fill all fields and submit"""
    document_type: str = Field("experience_certificate", description="Document type")
    employee_name: str = Field(..., description="Employee full name")
    position_title: str = Field(..., description="Job position title")
    department: str = Field(..., description="Department name")
    start_date: str = Field(..., description="Employment start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Employment end date (YYYY-MM-DD)")
    hr_manager_name: str = Field(..., description="HR manager name")
    company_name: str = Field(..., description="Company name")
    he_she: str = Field(..., description="He, She, or They")
    was_were: str = Field(..., description="was or were")
    output_format: str = Field("html", description="html, docx, or pdf")

# Dashboard Models - Updated
class DashboardMetrics(BaseModel):
    """Dashboard metrics response"""
    total_employees: int
    attrition_rate: float
    total_alerts: int
    appraisal_completion: float

class HeadcountResponse(BaseModel):
    """Headcount analytics response"""
    total_headcount: int
    by_department: Dict[str, int]
    by_role: Dict[str, int]
    last_updated: str

class AttritionResponse(BaseModel):
    """Attrition analytics response"""
    period_months: int
    total_terminations: int
    attrition_rate_percent: float
    by_department: Dict[str, int]
    last_updated: str

# ==================== INITIALIZATION ====================

gemini_key = os.getenv("GEMINI_API_KEY")
query_router = None
employee_services = None
leave_service = None
hr_analytics = None
performance_analytics = None
document_gen = None

def initialize_services():
    """Initialize all services"""
    global query_router, employee_services, leave_service, hr_analytics, performance_analytics, document_gen
    
    try:
        if gemini_key:
            query_router = HRQueryRouter(gemini_api_key=gemini_key)
            logger.info("✅ Query Router initialized")
        
        try:
            employee_services = EmployeeServicesManager()
            logger.info("✅ Employee Services initialized")
        except Exception as e:
            logger.warning(f"⚠️ Employee Services initialization failed: {e}")
        
        try:
            leave_service = LeaveManagementService()
            logger.info("✅ Leave Management Service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Leave Management Service initialization failed: {e}")
        
        try:
            hr_analytics = HRAnalyticsService()
            logger.info("✅ HR Analytics Service initialized")
        except Exception as e:
            logger.warning(f"⚠️ HR Analytics Service initialization failed: {e}")
        
        try:
            performance_analytics = PerformanceAnalyticsService()
            logger.info("✅ Performance Analytics Service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Performance Analytics Service initialization failed: {e}")
        
        try:
            document_gen = DocumentGenerator()
            logger.info("✅ Document Generator initialized")
        except Exception as e:
            logger.warning(f"⚠️ Document Generator initialization failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    initialize_services()
    logger.info("🚀 HR Assistant API started successfully")

# ==================== HEALTH CHECK ====================

@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "query_router": query_router is not None,
            "employee_services": employee_services is not None,
            "leave_service": leave_service is not None,
            "hr_analytics": hr_analytics is not None,
            "performance_analytics": performance_analytics is not None,
            "document_generator": document_gen is not None
        }
    }

# ==================== RAG QUERY ENDPOINTS ====================

@app.post("/api/query", response_model=Dict, tags=["RAG Query"])
async def ask_question(request: QueryRequest):
    """
    Submit a query to the RAG system
    
    The system intelligently routes to RAG or data queries based on content
    """
    if not query_router:
        raise HTTPException(status_code=503, detail="Query Router service not available")
    
    try:
        response = query_router.ask(
            query=request.query,
            is_urgent=request.is_urgent,
            user_role=request.user_role
        )
        return response
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query/router-info", tags=["RAG Query"])
async def get_router_info():
    """Get information about query routing patterns"""
    if not query_router:
        raise HTTPException(status_code=503, detail="Query Router service not available")
    
    try:
        return {
            "data_query_patterns": query_router.data_query_patterns,
            "document_generation_patterns": query_router.document_generation_patterns,
            "policy_query_keywords": query_router.policy_query_keywords
        }
    except Exception as e:
        logger.error(f"Router info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LEAVE MANAGEMENT ENDPOINTS ====================

@app.post("/api/leave/request", tags=["Leave Management"])
async def create_leave_request(request: LeaveRequestCreate):
    """Create a new leave request"""
    if not leave_service:
        raise HTTPException(status_code=503, detail="Leave Management service not available")
    
    try:
        result = leave_service.create_leave_request(
            employee_name=request.employee_name,
            employee_email=request.employee_email,
            leave_type=request.leave_type,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            emergency_contact=request.emergency_contact
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Leave request creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leave/employee/{employee_email}", tags=["Leave Management"])
async def get_employee_leave_requests(employee_email: str):
    """Get leave requests for an employee"""
    if not leave_service:
        raise HTTPException(status_code=503, detail="Leave Management service not available")
    
    try:
        requests = leave_service.get_employee_leave_requests(employee_email)
        return {"total": len(requests), "requests": requests}
    except Exception as e:
        logger.error(f"Get leave requests error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leave/all", tags=["Leave Management"])
async def get_all_leave_requests(status: Optional[str] = Query(None)):
    """Get all leave requests (HR view)"""
    if not leave_service:
        raise HTTPException(status_code=503, detail="Leave Management service not available")
    
    try:
        requests = leave_service.get_all_leave_requests(status=status)
        return {"total": len(requests), "requests": requests}
    except Exception as e:
        logger.error(f"Get all leave requests error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/leave/approve", tags=["Leave Management"])
async def approve_leave_request(request: LeaveApprovalRequest):
    """Approve or reject a leave request"""
    if not leave_service:
        raise HTTPException(status_code=503, detail="Leave Management service not available")
    
    try:
        result = leave_service.update_leave_request_status(
            request_id=request.request_id,
            status=request.status,
            hr_comments=request.hr_comments,
            hr_reviewer=request.hr_reviewer
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Leave approval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leave/statistics", tags=["Leave Management"])
async def get_leave_statistics():
    """Get leave statistics"""
    if not leave_service:
        raise HTTPException(status_code=503, detail="Leave Management service not available")
    
    try:
        stats = leave_service.get_leave_statistics()
        return stats
    except Exception as e:
        logger.error(f"Get leave statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EMPLOYEE SERVICES ENDPOINTS ====================

# Insurance Endpoints
@app.post("/api/employee-services/insurance/enroll", tags=["Employee Services - Insurance"])
async def enroll_insurance(request: InsuranceEnrollment):
    """Enroll employee in insurance plan"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        result = employee_services.enroll_employee_insurance(
            employee_email=request.employee_email,
            insurance_type=request.insurance_type,
            coverage_amount=request.coverage_amount,
            effective_date=request.effective_date,
            beneficiary_info={
                "name": request.beneficiary_name,
                "relation": request.beneficiary_relation
            } if request.beneficiary_name else {}
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Insurance enrollment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employee-services/insurance/{employee_email}", tags=["Employee Services - Insurance"])
async def get_employee_insurance(employee_email: str):
    """Get employee insurance records"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        insurance = employee_services.get_employee_insurance(employee_email)
        return {"total": len(insurance) if insurance else 0, "insurance": insurance or []}
    except Exception as e:
        logger.error(f"Get insurance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Shares Endpoints
@app.post("/api/employee-services/shares/allocate", tags=["Employee Services - Shares"])
async def allocate_shares(request: ShareAllocation):
    """Allocate shares to employee"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        result = employee_services.allocate_employee_shares(
            employee_email=request.employee_email,
            shares_count=request.shares_count,
            share_price=request.share_price,
            grant_date=request.grant_date,
            vesting_period_months=request.vesting_period_months
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Share allocation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employee-services/shares/{employee_email}", tags=["Employee Services - Shares"])
async def get_employee_shares(employee_email: str):
    """Get employee share records"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        shares = employee_services.get_employee_shares(employee_email)
        return {"total": len(shares) if shares else 0, "shares": shares or []}
    except Exception as e:
        logger.error(f"Get shares error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compliance Endpoints
@app.post("/api/employee-services/compliance/record", tags=["Employee Services - Compliance"])
async def record_compliance_training(request: ComplianceTraining):
    """Record compliance training"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        result = employee_services.record_compliance_training(
            employee_email=request.employee_email,
            training_type=request.training_type,
            completion_date=request.completion_date,
            expiry_date=request.expiry_date,
            certificate_url=request.certificate_url
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Compliance training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employee-services/compliance/{employee_email}", tags=["Employee Services - Compliance"])
async def get_compliance_status(employee_email: str):
    """Get employee compliance status"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        status = employee_services.get_employee_compliance_status(employee_email)
        return status
    except Exception as e:
        logger.error(f"Get compliance status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Governance Endpoints
@app.post("/api/employee-services/governance/role", tags=["Employee Services - Governance"])
async def create_governance_role(request: GovernanceRole):
    """Create governance role"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        result = employee_services.create_governance_role(
            role_name=request.role_name,
            department=request.department,
            responsibilities=request.responsibilities,
            reporting_to=request.reporting_to
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Governance role creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employee-services/governance/structure", tags=["Employee Services - Governance"])
async def get_organization_structure(department: Optional[str] = Query(None)):
    """Get organization structure"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        structure = employee_services.get_organization_structure(department)
        return {"total": len(structure) if structure else 0, "structure": structure or []}
    except Exception as e:
        logger.error(f"Get organization structure error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Career Development Endpoints
@app.post("/api/employee-services/development/plan", tags=["Employee Services - Career Development"])
async def create_development_plan(request: DevelopmentPlan):
    """Create development plan"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        result = employee_services.create_development_plan(
            employee_email=request.employee_email,
            plan_title=request.plan_title,
            goals=request.goals,
            timeline_months=request.timeline_months,
            mentor_email=request.mentor_email
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Development plan creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/employee-services/development/training", tags=["Employee Services - Career Development"])
async def record_training_completion(request: TrainingCompletion):
    """Record training completion"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        result = employee_services.record_training_completion(
            employee_email=request.employee_email,
            training_name=request.training_name,
            training_date=request.training_date,
            provider=request.provider,
            certificate_url=request.certificate_url
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    except Exception as e:
        logger.error(f"Training completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employee-services/development/{employee_email}", tags=["Employee Services - Career Development"])
async def get_development_profile(employee_email: str):
    """Get employee development profile"""
    if not employee_services:
        raise HTTPException(status_code=503, detail="Employee Services not available")
    
    try:
        profile = employee_services.get_employee_development_profile(employee_email)
        return profile
    except Exception as e:
        logger.error(f"Get development profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DOCUMENT GENERATION ENDPOINTS ====================

# Specific models for each document type - These show exact required fields in Swagger
class OfferLetterRequest(BaseModel):
    """Offer Letter - Fill all fields and submit"""
    document_type: str = Field("offer_letter", description="Document type")
    employee_name: str = Field(..., description="Employee full name")
    position_title: str = Field(..., description="Job position title")
    department: str = Field(..., description="Department name")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    salary: float = Field(..., description="Annual salary")
    employment_type: str = Field(..., description="Full-time, Part-time, or Contract")
    response_deadline: str = Field(..., description="Deadline (YYYY-MM-DD)")
    hr_manager_name: str = Field(..., description="HR manager name")
    company_name: str = Field(..., description="Company name")
    output_format: str = Field("html", description="html, docx, or pdf")

class TerminationLetterRequest(BaseModel):
    """Termination Letter - Fill all fields and submit"""
    document_type: str = Field("termination_letter", description="Document type")
    employee_name: str = Field(..., description="Employee full name")
    employee_id: str = Field(..., description="Employee ID")
    position_title: str = Field(..., description="Job position title")
    department: str = Field(..., description="Department name")
    termination_date: str = Field(..., description="Termination date (YYYY-MM-DD)")
    last_working_day: str = Field(..., description="Last working day (YYYY-MM-DD)")
    termination_reason: str = Field(..., description="Reason for termination")
    hr_manager_name: str = Field(..., description="HR manager name")
    company_name: str = Field(..., description="Company name")
    final_salary: Optional[float] = Field(None, description="Final salary (optional)")
    unused_leave_days: Optional[int] = Field(None, description="Unused leave days (optional)")
    unused_leave_amount: Optional[float] = Field(None, description="Leave amount (optional)")
    total_settlement: Optional[float] = Field(None, description="Total settlement (optional)")
    output_format: str = Field("html", description="html, docx, or pdf")

class ExperienceCertificateRequest(BaseModel):
    """Experience Certificate - Fill all fields and submit"""
    document_type: str = Field("experience_certificate", description="Document type")
    employee_name: str = Field(..., description="Employee full name")
    position_title: str = Field(..., description="Job position title")
    department: str = Field(..., description="Department name")
    start_date: str = Field(..., description="Employment start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Employment end date (YYYY-MM-DD)")
    hr_manager_name: str = Field(..., description="HR manager name")
    company_name: str = Field(..., description="Company name")
    he_she: str = Field(..., description="He, She, or They")
    was_were: str = Field(..., description="was or were")
    output_format: str = Field("html", description="html, docx, or pdf")

@app.post("/api/documents/generate", tags=["Document Generation"])
async def generate_offer_letter(request: OfferLetterRequest):
    """Generate Offer Letter - Select this when document_type is offer_letter"""
    if not document_gen:
        raise HTTPException(status_code=503, detail="Document Generator service not available")
    
    try:
        template_data = request.dict(exclude={"document_type", "output_format"})
        
        result = document_gen.generate_document(
            template_name="offer_letter",
            template_data=template_data,
            output_format=request.output_format
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return {
            "success": True,
            "filename": result.get('filename'),
            "document_type": "offer_letter",
            "format": request.output_format,
            "content": result.get('content'),
            "created_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/generate-termination", tags=["Document Generation"])
async def generate_termination_letter(request: TerminationLetterRequest):
    """Generate Termination Letter - Select this when document_type is termination_letter"""
    if not document_gen:
        raise HTTPException(status_code=503, detail="Document Generator service not available")
    
    try:
        template_data = request.dict(exclude={"document_type", "output_format"})
        
        result = document_gen.generate_document(
            template_name="termination_letter",
            template_data=template_data,
            output_format=request.output_format
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return {
            "success": True,
            "filename": result.get('filename'),
            "document_type": "termination_letter",
            "format": request.output_format,
            "content": result.get('content'),
            "created_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/generate-certificate", tags=["Document Generation"])
async def generate_experience_certificate(request: ExperienceCertificateRequest):
    """Generate Experience Certificate - Select this when document_type is experience_certificate"""
    if not document_gen:
        raise HTTPException(status_code=503, detail="Document Generator service not available")
    
    try:
        template_data = request.dict(exclude={"document_type", "output_format"})
        
        result = document_gen.generate_document(
            template_name="experience_certificate",
            template_data=template_data,
            output_format=request.output_format
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return {
            "success": True,
            "filename": result.get('filename'),
            "document_type": "experience_certificate",
            "format": request.output_format,
            "content": result.get('content'),
            "created_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/api/dashboard/metrics", tags=["Dashboard"])
async def get_dashboard_metrics():
    """
    Get key HR metrics summary
    
    Returns:
    - total_employees: Current active headcount
    - attrition_rate: Attrition rate percentage (last 3 months)
    - total_alerts: Combined probation + contract alerts
    - appraisal_completion: Appraisal completion rate percentage
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        summary = hr_analytics.get_hr_dashboard_summary()
        
        if 'error' in summary:
            raise HTTPException(status_code=500, detail=summary['error'])
        
        return {
            "metrics": summary.get('summary', {}),
            "last_updated": summary.get('last_updated', datetime.now().isoformat())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/headcount", tags=["Dashboard"])
async def get_headcount_analytics():
    """
    Get detailed headcount breakdown
    
    Returns:
    - total_headcount: Total active employees
    - by_department: Employee count per department
    - by_role: Employee count per role
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        headcount = hr_analytics.get_current_headcount()
        
        if 'error' in headcount:
            raise HTTPException(status_code=500, detail=headcount['error'])
        
        return headcount
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get headcount error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/headcount/trends", tags=["Dashboard"])
async def get_headcount_trends(months: int = Query(6, description="Number of months to analyze")):
    """
    Get headcount trends over time
    
    Returns monthly hiring and termination data
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        trends = hr_analytics.get_headcount_trends(months=months)
        
        if 'error' in trends:
            raise HTTPException(status_code=500, detail=trends['error'])
        
        return trends
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get headcount trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/attrition", tags=["Dashboard"])
async def get_attrition_analytics(months: int = Query(12, description="Period in months")):
    """
    Get attrition analysis
    
    Returns:
    - total_terminations: Number of departures
    - attrition_rate_percent: Attrition rate
    - by_department: Departures per department
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        attrition = hr_analytics.get_attrition_data(period_months=months)
        
        if 'error' in attrition:
            raise HTTPException(status_code=500, detail=attrition['error'])
        
        return attrition
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get attrition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/probation", tags=["Dashboard"])
async def get_probation_alerts():
    """
    Get probation review alerts
    
    Returns:
    - upcoming_reviews: Employees with probation ending within 14 days
    - overdue_reviews: Employees with overdue probation reviews
    - total_alerts: Total probation alerts
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        probation = hr_analytics.get_probation_alerts()
        
        if 'error' in probation:
            raise HTTPException(status_code=500, detail=probation['error'])
        
        return probation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get probation alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/appraisals", tags=["Dashboard"])
async def get_appraisal_status():
    """
    Get current appraisal cycle status
    
    Returns:
    - cycle_info: Current cycle details
    - completion_stats: Completion rate and counts
    - by_department: Department-wise completion
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        appraisals = hr_analytics.get_appraisal_status()
        
        if 'error' in appraisals:
            raise HTTPException(status_code=500, detail=appraisals['error'])
        
        return appraisals
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get appraisal status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/contracts", tags=["Dashboard"])
async def get_contract_alerts(days: int = Query(30, description="Days ahead to check")):
    """
    Get contract expiry alerts
    
    Returns:
    - expiring_contracts: List of contracts expiring soon
    - total_expiring: Count of expiring contracts
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        contracts = hr_analytics.get_contract_expiry_alerts(days_ahead=days)
        
        if 'error' in contracts:
            raise HTTPException(status_code=500, detail=contracts['error'])
        
        return contracts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get contract alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/performance", tags=["Dashboard"])
async def get_performance_rankings(
    quarter: str = Query(None, description="Quarter (Q1, Q2, Q3, Q4)"),
    year: int = Query(None, description="Year")
):
    """
    Get quarterly performance rankings
    
    Returns:
    - overall_rankings: Employees ranked by performance
    - department_rankings: Rankings by department
    - performance_distribution: Tier distribution
    """
    if not performance_analytics:
        raise HTTPException(status_code=503, detail="Performance Analytics service not available")
    
    try:
        rankings = performance_analytics.get_quarterly_rankings(quarter=quarter, year=year)
        
        if 'error' in rankings:
            raise HTTPException(status_code=500, detail=rankings['error'])
        
        return rankings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get performance rankings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/performance/distribution", tags=["Dashboard"])
async def get_performance_distribution():
    """
    Get performance tier distribution
    
    Returns performance distribution across all employees
    """
    if not performance_analytics:
        raise HTTPException(status_code=503, detail="Performance Analytics service not available")
    
    try:
        employees = performance_analytics.get_employee_performance_data()
        
        if not employees:
            return {
                "distribution": {},
                "total_employees": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        # Calculate scores and tiers
        for emp in employees:
            emp['calculated_score'] = performance_analytics.calculate_performance_score(emp)
            emp['performance_tier'] = performance_analytics.get_performance_tier(emp['calculated_score'])
        
        distribution = performance_analytics.get_performance_distribution(employees)
        
        return {
            "distribution": distribution,
            "total_employees": len(employees),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get performance distribution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/performance/employee/{employee_id}", tags=["Dashboard"])
async def get_employee_performance_detail(employee_id: str):
    """
    Get detailed performance profile for an employee
    
    Returns:
    - employee_profile: Basic info and scores
    - performance_breakdown: Score by criteria
    - peer_comparison: Comparison with department peers
    - strengths: Top performing areas
    - improvement_areas: Areas needing development
    """
    if not performance_analytics:
        raise HTTPException(status_code=503, detail="Performance Analytics service not available")
    
    try:
        detail = performance_analytics.get_employee_detail(employee_id)
        
        if 'error' in detail:
            raise HTTPException(status_code=404, detail=detail['error'])
        
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get employee performance detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/summary", tags=["Dashboard"])
async def get_dashboard_summary():
    """
    Get complete HR dashboard summary
    
    Returns all dashboard data in a single response:
    - summary: Key metrics
    - headcount: Headcount breakdown
    - attrition: Attrition analysis
    - probation_alerts: Probation reviews
    - appraisal_status: Appraisal completion
    - contract_alerts: Expiring contracts
    """
    if not hr_analytics:
        raise HTTPException(status_code=503, detail="HR Analytics service not available")
    
    try:
        summary = hr_analytics.get_hr_dashboard_summary()
        
        if 'error' in summary:
            raise HTTPException(status_code=500, detail=summary['error'])
        
        return {
            "timestamp": datetime.now().isoformat(),
            **summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dashboard summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ROOT ENDPOINT ====================

@app.get("/", tags=["System"])
async def root():
    """API documentation and information"""
    return {
        "name": "HR Assistant API",
        "version": "1.0.0",
        "description": "Comprehensive HR Management System with RAG, Employee Services, Leave Management, and Document Generation",
        "documentation": "/api/docs",
        "redoc": "/api/redoc",
        "endpoints": {
            "rag_query": "/api/query",
            "leave_management": "/api/leave/*",
            "employee_services": "/api/employee-services/*",
            "documents": "/api/documents/*",
            "dashboard": "/api/dashboard/*",
            "health": "/api/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
