# -*- coding: utf-8 -*-
"""
Employee Services Management
Handles Insurance, Shares, Compliance, Governance, and Career Development
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, date
from supabase import Client
from knowledge_base import HRKnowledgeBaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmployeeServicesManager:
    """Manager for employee services and benefits"""
    
    def __init__(self):
        """Initialize with Supabase client"""
        kb_client = HRKnowledgeBaseClient()
        self.supabase = kb_client.supabase
        logger.info("Employee Services Manager initialized")
    
    # ==================== INSURANCE MANAGEMENT ====================
    
    def enroll_employee_insurance(self, employee_email: str, insurance_type: str,
                                 coverage_amount: float, effective_date: date,
                                 beneficiary_info: Dict) -> Dict:
        """Enroll employee in insurance plan"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found'}
            
            person_id = person_result.data[0]['id']
            
            insurance_data = {
                'person_id': person_id,
                'insurance_type': insurance_type,  # health, life, dental, vision
                'coverage_amount': coverage_amount,
                'effective_date': effective_date.isoformat(),
                'status': 'active',
                'beneficiary_info': beneficiary_info,
                'enrollment_date': datetime.now().isoformat()
            }
            
            result = self.supabase.table('employee_insurance').insert(insurance_data).execute()
            
            if result.data:
                logger.info(f"Insurance enrolled for {employee_email}: {insurance_type}")
                return {
                    'success': True,
                    'insurance_id': result.data[0]['id'],
                    'message': f'{insurance_type} insurance enrolled successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to enroll insurance'}
                
        except Exception as e:
            logger.error(f"Error enrolling insurance: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_employee_insurance(self, employee_email: str) -> List[Dict]:
        """Get all insurance details for an employee"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return []
            
            person_id = person_result.data[0]['id']
            
            result = self.supabase.table('employee_insurance').select(
                'id, insurance_type, coverage_amount, effective_date, status, beneficiary_info, enrollment_date'
            ).eq('person_id', person_id).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting insurance for {employee_email}: {e}")
            return []
    
    # ==================== EMPLOYEE SHARES MANAGEMENT ====================
    
    def allocate_employee_shares(self, employee_email: str, shares_count: int,
                                share_price: float, grant_date: date,
                                vesting_period_months: int = 48) -> Dict:
        """Allocate shares/stock options to employee"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found'}
            
            person_id = person_result.data[0]['id']
            
            # Calculate vesting schedule (4-year vesting with 1-year cliff is common)
            cliff_months = 12
            
            shares_data = {
                'person_id': person_id,
                'total_shares': shares_count,
                'vested_shares': 0,
                'share_price': share_price,
                'grant_date': grant_date.isoformat(),
                'vesting_period_months': vesting_period_months,
                'cliff_months': cliff_months,
                'status': 'active'
            }
            
            result = self.supabase.table('employee_shares').insert(shares_data).execute()
            
            if result.data:
                logger.info(f"Shares allocated to {employee_email}: {shares_count} shares")
                return {
                    'success': True,
                    'share_grant_id': result.data[0]['id'],
                    'message': f'{shares_count} shares allocated successfully',
                    'vesting_period': f'{vesting_period_months} months',
                    'total_value': result.data[0].get('total_value', shares_count * share_price)
                }
            else:
                return {'success': False, 'error': 'Failed to allocate shares'}
                
        except Exception as e:
            logger.error(f"Error allocating shares: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_employee_shares(self, employee_email: str) -> List[Dict]:
        """Get share allocations for an employee"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return []
            
            person_id = person_result.data[0]['id']
            
            result = self.supabase.table('employee_shares').select(
                'id, total_shares, vested_shares, share_price, grant_date, vesting_period_months, cliff_months, status'
            ).eq('person_id', person_id).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting shares for {employee_email}: {e}")
            return []
    
    # ==================== COMPLIANCE MANAGEMENT ====================
    
    def record_compliance_training(self, employee_email: str, training_type: str,
                                  completion_date: date, expiry_date: date,
                                  certificate_url: str = None) -> Dict:
        """Record employee compliance training"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found'}
            
            person_id = person_result.data[0]['id']
            
            compliance_data = {
                'person_id': person_id,
                'training_type': training_type,  # GDPR, HIPAA, Anti-Corruption, etc.
                'completion_date': completion_date.isoformat(),
                'expiry_date': expiry_date.isoformat(),
                'certificate_url': certificate_url,
                'status': 'completed',
                'recorded_date': datetime.now().isoformat()
            }
            
            result = self.supabase.table('compliance_training').insert(compliance_data).execute()
            
            if result.data:
                logger.info(f"Compliance training recorded for {employee_email}: {training_type}")
                return {
                    'success': True,
                    'training_id': result.data[0]['id'],
                    'message': f'{training_type} compliance training recorded'
                }
            else:
                return {'success': False, 'error': 'Failed to record training'}
                
        except Exception as e:
            logger.error(f"Error recording compliance training: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_employee_compliance_status(self, employee_email: str) -> Dict:
        """Get compliance status for an employee"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {}
            
            person_id = person_result.data[0]['id']
            
            result = self.supabase.table('compliance_training').select(
                'training_type, completion_date, expiry_date, status'
            ).eq('person_id', person_id).order('expiry_date', desc=False).execute()
            
            # Check for expired trainings
            compliant_trainings = []
            expired_trainings = []
            
            for training in result.data:
                expiry = datetime.fromisoformat(training['expiry_date']).date()
                if expiry < date.today():
                    expired_trainings.append(training)
                else:
                    compliant_trainings.append(training)
            
            return {
                'employee_email': employee_email,
                'compliant_trainings': compliant_trainings,
                'expired_trainings': expired_trainings,
                'compliance_status': 'compliant' if not expired_trainings else 'non-compliant'
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance status for {employee_email}: {e}")
            return {'error': str(e)}
    
    # ==================== GOVERNANCE STRUCTURE ====================
    
    def create_governance_role(self, role_name: str, department: str,
                              responsibilities: List[str], reporting_to: str) -> Dict:
        """Create a governance role in the organization"""
        try:
            # Find the manager/reporting_to person
            manager_result = self.supabase.table('people').select('id').ilike(
                'display_name', f'%{reporting_to}%'
            ).limit(1).execute()
            
            manager_id = None
            if manager_result.data:
                manager_id = manager_result.data[0]['id']
            
            governance_data = {
                'role_name': role_name,
                'department': department,
                'responsibilities': responsibilities,
                'manager_id': manager_id,
                'created_date': datetime.now().isoformat()
            }
            
            result = self.supabase.table('governance_roles').insert(governance_data).execute()
            
            if result.data:
                logger.info(f"Governance role created: {role_name}")
                return {
                    'success': True,
                    'role_id': result.data[0]['id'],
                    'message': f'Governance role "{role_name}" created successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to create governance role'}
                
        except Exception as e:
            logger.error(f"Error creating governance role: {e}")
            return {'success': False, 'error': str(e)}
    
    def assign_employee_to_role(self, employee_email: str, role_id: str) -> Dict:
        """Assign an employee to a governance role"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found'}
            
            person_id = person_result.data[0]['id']
            
            assignment_data = {
                'person_id': person_id,
                'role_id': role_id,
                'assignment_date': datetime.now().isoformat(),
                'status': 'active'
            }
            
            result = self.supabase.table('role_assignments').insert(assignment_data).execute()
            
            if result.data:
                logger.info(f"Employee {employee_email} assigned to role {role_id}")
                return {
                    'success': True,
                    'assignment_id': result.data[0]['id'],
                    'message': 'Employee assigned to role successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to assign role'}
                
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_organization_structure(self, department: str = None) -> List[Dict]:
        """Get governance structure for organization or department"""
        try:
            # Query governance_roles directly (shows all roles)
            query = self.supabase.table('governance_roles').select('''
                id, role_name, department, responsibilities, manager_id, created_date,
                manager:people!governance_roles_manager_id_fkey(first_name, last_name, work_email),
                role_assignments(person_id, people!role_assignments_person_id_fkey(first_name, last_name, work_email))
            ''')
            
            if department:
                query = query.eq('department', department)
            
            result = query.order('department').execute()
            
            if not result.data:
                logger.warning(f"No governance roles found for department: {department}")
                return []
            
            structure = []
            for role in result.data:
                manager = role.get('manager', {})
                assignments = role.get('role_assignments', [])
                
                # If role has assignments, create entry for each assigned person
                if assignments:
                    for assignment in assignments:
                        person = assignment.get('people', {})
                        structure.append({
                            'role_id': role['id'],
                            'role_name': role['role_name'],
                            'department': role['department'],
                            'responsibilities': role.get('responsibilities', []),
                            'employee_name': f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                            'employee_email': person.get('work_email', ''),
                            'reports_to_manager': f"{manager.get('first_name', '')} {manager.get('last_name', '')}".strip() if manager else 'Unassigned',
                            'manager_email': manager.get('work_email') if manager else None,
                            'assignment_status': 'assigned',
                            'created_date': role.get('created_date')
                        })
                else:
                    # If role has no assignments, show the role as unassigned
                    structure.append({
                        'role_id': role['id'],
                        'role_name': role['role_name'],
                        'department': role['department'],
                        'responsibilities': role.get('responsibilities', []),
                        'employee_name': None,
                        'employee_email': None,
                        'reports_to_manager': f"{manager.get('first_name', '')} {manager.get('last_name', '')}".strip() if manager else 'Unassigned',
                        'manager_email': manager.get('work_email') if manager else None,
                        'assignment_status': 'vacant',
                        'created_date': role.get('created_date')
                    })
            
            logger.info(f"Retrieved {len(structure)} organization structure entries")
            return structure
            
        except Exception as e:
            logger.error(f"Error getting organization structure: {e}")
            return []
    
    # ==================== CAREER DEVELOPMENT ====================
    
    def create_development_plan(self, employee_email: str, plan_title: str,
                               goals: List[Dict], timeline_months: int,
                               mentor_email: str = None) -> Dict:
        """Create career development plan for employee"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found'}
            
            person_id = person_result.data[0]['id']
            
            # Get mentor ID if provided
            mentor_id = None
            if mentor_email:
                mentor_result = self.supabase.table('people').select('id').eq('work_email', mentor_email).execute()
                if mentor_result.data:
                    mentor_id = mentor_result.data[0]['id']
            
            development_data = {
                'person_id': person_id,
                'plan_title': plan_title,
                'goals': goals,
                'timeline_months': timeline_months,
                'mentor_id': mentor_id,
                'start_date': datetime.now().isoformat(),
                'status': 'active'
            }
            
            result = self.supabase.table('career_development_plans').insert(development_data).execute()
            
            if result.data:
                logger.info(f"Development plan created for {employee_email}: {plan_title}")
                return {
                    'success': True,
                    'plan_id': result.data[0]['id'],
                    'message': f'Career development plan "{plan_title}" created successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to create development plan'}
                
        except Exception as e:
            logger.error(f"Error creating development plan: {e}")
            return {'success': False, 'error': str(e)}
    
    def record_training_completion(self, employee_email: str, training_name: str,
                                  training_date: date, provider: str,
                                  certificate_url: str = None) -> Dict:
        """Record employee training completion"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {'success': False, 'error': f'Employee with email {employee_email} not found'}
            
            person_id = person_result.data[0]['id']
            
            training_data = {
                'person_id': person_id,
                'training_name': training_name,
                'training_date': training_date.isoformat(),
                'provider': provider,
                'certificate_url': certificate_url,
                'recorded_date': datetime.now().isoformat()
            }
            
            result = self.supabase.table('employee_training').insert(training_data).execute()
            
            if result.data:
                logger.info(f"Training recorded for {employee_email}: {training_name}")
                return {
                    'success': True,
                    'training_id': result.data[0]['id'],
                    'message': f'Training "{training_name}" recorded successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to record training'}
                
        except Exception as e:
            logger.error(f"Error recording training: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_employee_development_profile(self, employee_email: str) -> Dict:
        """Get complete career development profile for an employee"""
        try:
            person_result = self.supabase.table('people').select('id').eq('work_email', employee_email).execute()
            
            if not person_result.data:
                return {}
            
            person_id = person_result.data[0]['id']
            
            # Get development plans
            plans = self.supabase.table('career_development_plans').select(
                'id, plan_title, goals, timeline_months, start_date, status'
            ).eq('person_id', person_id).execute().data or []
            
            # Get completed trainings
            trainings = self.supabase.table('employee_training').select(
                'training_name, training_date, provider, certificate_url'
            ).eq('person_id', person_id).order('training_date', desc=True).execute().data or []
            
            return {
                'employee_email': employee_email,
                'development_plans': plans,
                'completed_trainings': trainings,
                'total_trainings': len(trainings),
                'profile_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting development profile for {employee_email}: {e}")
            return {'error': str(e)}