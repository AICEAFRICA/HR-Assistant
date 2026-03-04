# -*- coding: utf-8 -*-
"""
Leave Management Service for Employee Leave Requests and HR Approvals
Uses existing leave_request table from Supabase schema
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from supabase import Client
from knowledge_base import HRKnowledgeBaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeaveManagementService:
    """Service for managing employee leave requests using existing schema"""
    
    def __init__(self):
        """Initialize with Supabase client"""
        kb_client = HRKnowledgeBaseClient()
        self.supabase = kb_client.supabase
        logger.info("Leave Management Service initialized")
    
    def create_leave_request(self, employee_name: str, employee_email: str, 
                           leave_type: str, start_date: date, end_date: date, 
                           reason: str, emergency_contact: str = None) -> Dict:
        """Create a new leave request using existing schema"""
        try:
            # Find person by email
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found in system'}
            
            person_id = person_result.data[0]['id']
            
            # Create leave request using your schema
            leave_data = {
                'person_id': person_id,
                'leave_type': leave_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'reason': reason,
                'status': 'pending'
            }
            
            result = self.supabase.table('leave_request').insert(leave_data).execute()
            
            if result.data:
                request_id = result.data[0]['id']
                logger.info(f"Leave request created: {request_id} for {employee_name}")
                return {
                    'success': True,
                    'request_id': request_id,
                    'message': f'Leave request submitted successfully. Request ID: {request_id}'
                }
            else:
                return {'success': False, 'error': 'Failed to create leave request'}
                
        except Exception as e:
            logger.error(f"Error creating leave request: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_employee_leave_requests(self, employee_email: str) -> List[Dict]:
        """Get all leave requests for a specific employee using existing schema"""
        try:
            # Get person_id first
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return []
            
            person_id = person_result.data[0]['id']
            
            # Get leave requests with person details
            result = self.supabase.table('leave_request').select('''
                id, leave_type, start_date, end_date, status, reason, created_at,
                people!leave_request_person_id_fkey(first_name, last_name, work_email),
                approver:people!leave_request_approver_id_fkey(first_name, last_name)
            ''').eq('person_id', person_id).order('created_at', desc=True).execute()
            
            # Format the data for display
            formatted_requests = []
            for req in result.data:
                person = req.get('people', {})
                approver = req.get('approver', {})
                
                # Calculate days
                start = datetime.fromisoformat(req['start_date']).date()
                end = datetime.fromisoformat(req['end_date']).date()
                days_requested = (end - start).days + 1
                
                formatted_requests.append({
                    'id': req['id'],
                    'employee_name': f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    'employee_email': person.get('work_email', ''),
                    'leave_type': req['leave_type'],
                    'start_date': req['start_date'],
                    'end_date': req['end_date'],
                    'days_requested': days_requested,
                    'reason': req.get('reason', ''),
                    'status': req['status'],
                    'request_date': req['created_at'],
                    'hr_reviewer': f"{approver.get('first_name', '')} {approver.get('last_name', '')}".strip() if approver else None,
                    'review_date': None,  # Not in current schema
                    'hr_comments': None   # Not in current schema
                })
            
            return formatted_requests
            
        except Exception as e:
            logger.error(f"Error getting leave requests for {employee_email}: {e}")
            return []
    
    def get_all_leave_requests(self, status: str = None) -> List[Dict]:
        """Get all leave requests (HR view) using existing schema"""
        try:
            query = self.supabase.table('leave_request').select('''
                id, leave_type, start_date, end_date, status, reason, created_at,
                people!leave_request_person_id_fkey(first_name, last_name, work_email),
                approver:people!leave_request_approver_id_fkey(first_name, last_name)
            ''')
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).execute()
            
            # Format the data for display
            formatted_requests = []
            for req in result.data:
                person = req.get('people', {})
                approver = req.get('approver', {})
                
                # Calculate days
                start = datetime.fromisoformat(req['start_date']).date()
                end = datetime.fromisoformat(req['end_date']).date()
                days_requested = (end - start).days + 1
                
                formatted_requests.append({
                    'id': req['id'],
                    'employee_name': f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    'employee_email': person.get('work_email', ''),
                    'leave_type': req['leave_type'],
                    'start_date': req['start_date'],
                    'end_date': req['end_date'],
                    'days_requested': days_requested,
                    'reason': req.get('reason', ''),
                    'status': req['status'],
                    'request_date': req['created_at'],
                    'hr_reviewer': f"{approver.get('first_name', '')} {approver.get('last_name', '')}".strip() if approver else None
                })
            
            return formatted_requests
            
        except Exception as e:
            logger.error(f"Error getting all leave requests: {e}")
            return []
    
    def update_leave_request_status(self, request_id: str, status: str, 
                                  hr_comments: str = None, hr_reviewer: str = None) -> Dict:
        """Update leave request status (approve/reject) using existing schema"""
        try:
            # Find the HR reviewer by name (simple approach)
            # In a production system, you'd want to use the logged-in user's ID
            approver_id = None
            if hr_reviewer:
                approver_result = self.supabase.table('people').select('id').ilike(
                    'display_name', f'%{hr_reviewer}%'
                ).limit(1).execute()
                
                if approver_result.data:
                    approver_id = approver_result.data[0]['id']
            
            update_data = {'status': status}
            if approver_id:
                update_data['approver_id'] = approver_id
            
            result = self.supabase.table('leave_request').update(
                update_data
            ).eq('id', request_id).execute()
            
            if result.data:
                logger.info(f"Leave request {request_id} updated to {status}")
                
                # Store HR comments in a notification or audit log if needed
                if hr_comments:
                    try:
                        # Create a notification for the employee about the decision
                        leave_req = self.supabase.table('leave_request').select(
                            'person_id, people!leave_request_person_id_fkey(first_name, last_name)'
                        ).eq('id', request_id).execute()
                        
                        if leave_req.data:
                            person_data = leave_req.data[0]
                            person_name = f"{person_data['people']['first_name']} {person_data['people']['last_name']}"
                            
                            notification_data = {
                                'person_id': person_data['person_id'],
                                'title': f'Leave Request {status.title()}',
                                'body': f'Your leave request has been {status}. HR Comments: {hr_comments}',
                                'channel': 'email',
                                'status': 'queued'
                            }
                            
                            self.supabase.table('notification').insert(notification_data).execute()
                    except Exception as e:
                        logger.warning(f"Could not create notification: {e}")
                
                return {
                    'success': True,
                    'message': f'Leave request {status} successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to update leave request'}
                
        except Exception as e:
            logger.error(f"Error updating leave request {request_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_leave_statistics(self) -> Dict:
        """Get leave statistics for HR dashboard using existing schema"""
        try:
            # Get all requests
            all_requests = self.get_all_leave_requests()
            
            # Calculate statistics
            total_requests = len(all_requests)
            pending_requests = len([r for r in all_requests if r['status'] == 'pending'])
            approved_requests = len([r for r in all_requests if r['status'] == 'approved'])
            rejected_requests = len([r for r in all_requests if r['status'] == 'rejected'])
            
            # Leave types breakdown
            leave_types = {}
            for request in all_requests:
                leave_type = request.get('leave_type', 'Unknown')
                leave_types[leave_type] = leave_types.get(leave_type, 0) + 1
            
            # This month's requests
            current_month = datetime.now().strftime('%Y-%m')
            this_month_requests = len([
                r for r in all_requests 
                if r.get('request_date', '').startswith(current_month)
            ])
            
            return {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'approved_requests': approved_requests,
                'rejected_requests': rejected_requests,
                'this_month_requests': this_month_requests,
                'leave_types_breakdown': leave_types,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting leave statistics: {e}")
            return {'error': str(e)}
    
    def get_leave_requests_for_manager(self, manager_email: str) -> List[Dict]:
        """Get leave requests for employees reporting to a specific manager"""
        try:
            # Find manager by email
            manager_result = self.supabase.table('people').select('id').eq('work_email', manager_email).execute()
            
            if not manager_result.data:
                return []
            
            manager_id = manager_result.data[0]['id']
            
            # Get leave requests for team members
            result = self.supabase.table('leave_request').select('''
                id, leave_type, start_date, end_date, status, reason, created_at,
                people!leave_request_person_id_fkey(first_name, last_name, work_email, manager_id)
            ''').execute()
            
            # Filter for manager's direct reports
            manager_requests = []
            for req in result.data:
                person = req.get('people', {})
                if person.get('manager_id') == manager_id:
                    # Calculate days
                    start = datetime.fromisoformat(req['start_date']).date()
                    end = datetime.fromisoformat(req['end_date']).date()
                    days_requested = (end - start).days + 1
                    
                    manager_requests.append({
                        'id': req['id'],
                        'employee_name': f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                        'employee_email': person.get('work_email', ''),
                        'leave_type': req['leave_type'],
                        'start_date': req['start_date'],
                        'end_date': req['end_date'],
                        'days_requested': days_requested,
                        'reason': req.get('reason', ''),
                        'status': req['status'],
                        'request_date': req['created_at']
                    })
            
            return manager_requests
            
        except Exception as e:
            logger.error(f"Error getting leave requests for manager {manager_email}: {e}")
            return []
