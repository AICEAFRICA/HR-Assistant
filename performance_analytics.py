# -*- coding: utf-8 -*-
"""
Performance Analytics Service for Quarterly Organizational Index
Handles employee performance tracking, ranking, and detailed profiles - Database Backed
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
from supabase import Client
from knowledge_base import HRKnowledgeBaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceAnalyticsService:
    """Service for employee performance analytics and quarterly index"""
    
    def __init__(self):
        """Initialize with Supabase client"""
        kb_client = HRKnowledgeBaseClient()
        self.supabase = kb_client.supabase
        logger.info("Performance Analytics Service initialized")
        
        # Load performance criteria weights from database
        self.performance_weights = self._load_performance_weights()
        
        # Simple cache
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_from_cache(self, key: str):
        """Get data from cache if not expired"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if (datetime.now().timestamp() - timestamp) < self._cache_ttl:
                return self._cache[key]
        return None

    def _set_cache(self, key: str, data):
        """Set data in cache"""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.now().timestamp()

    def _load_performance_weights(self) -> Dict[str, float]:
        """Load performance criteria weights from database"""
        try:
            result = self.supabase.table('performance_criteria').select('name, weight_percentage').eq('is_active', True).execute()
            
            weights = {}
            for criteria in result.data:
                weights[criteria['name']] = criteria['weight_percentage'] / 100
            
            return weights
            
        except Exception as e:
            logger.error(f"Error loading performance weights: {e}")
            # Fallback to default weights
            return {
                'job_knowledge': 0.20,
                'quality_of_work': 0.20,
                'productivity': 0.15,
                'communication': 0.15,
                'initiative': 0.10,
                'attendance_punctuality': 0.10,
                'engagement': 0.10
            }

    # CORE DATA RETRIEVAL METHODS
    def get_employee_performance_data(self) -> List[Dict]:
        """Get comprehensive employee performance data from database - CACHED"""
        # Check cache first
        cached_data = self._get_from_cache('employee_performance_data')
        if cached_data is not None:
            logger.info("Using cached employee performance data")
            return cached_data
        
        # If not in cache, fetch from database
        data = self._fetch_employee_performance_data()
        self._set_cache('employee_performance_data', data)
        return data

    def _fetch_employee_performance_data(self) -> List[Dict]:
        """Fetch employee performance data from database"""
        try:
            # Get current active appraisal cycle
            cycle_result = self.supabase.table('appraisal_cycle').select('*').order('created_at', desc=True).limit(1).execute()
            
            current_cycle = None
            cycle_id = None
            
            if cycle_result.data:
                current_cycle = cycle_result.data[0]
                cycle_id = current_cycle['id']
            else:
                logger.warning("No active appraisal cycle found")
            
            try:
                # FIXED: Simplified query without problematic relationships
                people_result = self.supabase.table('people').select('''
                    id, first_name, last_name, work_email, phone, started_on, employment_status, 
                    org_unit_id, manager_id
                ''').eq('employment_status', 'active').execute()
                
                if not people_result.data:
                    logger.warning("No active employees found")
                    return []
                
                # Get all person IDs for batch queries
                person_ids = [person['id'] for person in people_result.data]
                
                # Batch query for org units
                org_units = {}
                if person_ids:
                    org_unit_ids = list(set([p.get('org_unit_id') for p in people_result.data if p.get('org_unit_id')]))
                    if org_unit_ids:
                        org_result = self.supabase.table('org_unit').select('id, name').in_('id', org_unit_ids).execute()
                        org_units = {ou['id']: ou['name'] for ou in org_result.data}
                
                # Batch query for managers
                managers = {}
                manager_ids = list(set([p.get('manager_id') for p in people_result.data if p.get('manager_id')]))
                if manager_ids:
                    mgr_result = self.supabase.table('people').select('id, first_name, last_name').in_('id', manager_ids).execute()
                    managers = {mgr['id']: f"{mgr['first_name']} {mgr['last_name']}" for mgr in mgr_result.data}
                
                # Batch query for employment contracts
                contracts = {}
                contract_result = self.supabase.table('employment_contract').select(
                    'person_id, contract_type, base_salary, end_date'
                ).in_('person_id', person_ids).execute()
                contracts = {c['person_id']: c for c in contract_result.data}
                
                # Batch query for performance records
                performance_records = {}
                if cycle_id:
                    perf_result = self.supabase.table('employee_performance_record').select(
                        'person_id, criteria_scores, overall_score, performance_tier, engagement_percentage, remarks, last_review_date, next_review_date'
                    ).eq('appraisal_cycle_id', cycle_id).in_('person_id', person_ids).execute()
                    performance_records = {pr['person_id']: pr for pr in perf_result.data}
                
                # Batch query for attendance data
                start_date = (datetime.now() - timedelta(days=90)).date()
                attendance_result = self.supabase.table('attendance').select(
                    'person_id, work_date, check_in, check_out'
                ).in_('person_id', person_ids).gte('work_date', start_date).execute()
                
                # Create attendance lookup dictionary
                attendance_by_person = {}
                for record in attendance_result.data:
                    person_id = record['person_id']
                    if person_id not in attendance_by_person:
                        attendance_by_person[person_id] = []
                    attendance_by_person[person_id].append(record)
                
                employees = []
                for i, person in enumerate(people_result.data):
                    person_id = person['id']
                    
                    # Get department name from lookup
                    dept_name = org_units.get(person.get('org_unit_id'), 'Unknown')
                    
                    # Get manager name from lookup
                    manager_name = managers.get(person.get('manager_id'), 'Unknown')
                    
                    # Get contract info from lookup
                    contract = contracts.get(person_id, {})
                    contract_type = contract.get('contract_type', 'Full-time')
                    salary = contract.get('base_salary', 50000)
                    contract_end = contract.get('end_date')
                    
                    # Get performance record from lookup
                    performance_record = performance_records.get(person_id)
                    
                    # Calculate attendance score using cached data
                    attendance_score = self.calculate_attendance_score_from_data(
                        attendance_by_person.get(person_id, [])
                    )
                    
                    # Build employee data with proper type conversion
                    criteria_scores = performance_record.get('criteria_scores', {}) if performance_record else {}
                    engagement_percentage = int(performance_record.get('engagement_percentage', 80)) if performance_record else 80
                    
                    employee_data = {
                        'employee_id': f'ADL-{str(i+1).zfill(3)}',
                        'person_id': person_id,
                        'full_name': f"{person['first_name']} {person['last_name']}",
                        'email': person.get('work_email', ''),
                        'phone_number': person.get('phone', ''),
                        'department': dept_name,
                        'role_position': 'Employee',  # Default role
                        'employment_type': contract_type,
                        'reporting_manager': manager_name,
                        'start_date': person.get('started_on'),
                        'contract_end_date': contract_end,
                        'status': person.get('employment_status', 'active'),
                        'salary_kes': int(salary or 0),
                        'last_review_date': performance_record.get('last_review_date') if performance_record else None,
                        'next_review_date': performance_record.get('next_review_date') if performance_record else None,
                        'engagement_percentage': engagement_percentage,
                        'remarks': performance_record.get('remarks', '') if performance_record else '',
                        # Individual criteria scores with defaults (ensure all are floats)
                        'job_knowledge': float(criteria_scores.get('job_knowledge', 3)),
                        'quality_of_work': float(criteria_scores.get('quality_of_work', 3)),
                        'productivity': float(criteria_scores.get('productivity', 3)),
                        'communication': float(criteria_scores.get('communication', 3)),
                        'initiative': float(criteria_scores.get('initiative', 3)),
                        'attendance_punctuality': float(attendance_score),
                    }
                    
                    # Calculate performance score
                    if performance_record and performance_record.get('overall_score'):
                        employee_data['performance_score'] = float(performance_record.get('overall_score'))
                    else:
                        employee_data['performance_score'] = self.calculate_performance_score(employee_data)
                    
                    employees.append(employee_data)
                
                logger.info(f"Loaded {len(employees)} employees with optimized queries")
                return employees
                
            except Exception as db_error:
                logger.error(f"Database query failed: {db_error}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return []

    # ATTENDANCE CALCULATION METHODS
    def calculate_attendance_score_from_data(self, attendance_records: List[Dict], days: int = 90) -> float:
        """Calculate attendance score from pre-loaded attendance data"""
        try:
            if not attendance_records:
                return 3.0  # Default score if no attendance data
            
            # Calculate working days (excluding weekends)
            start_date = (datetime.now() - timedelta(days=days)).date()
            total_working_days = 0
            current_date = start_date
            while current_date <= datetime.now().date():
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    total_working_days += 1
                current_date += timedelta(days=1)
            
            # Calculate present days and on-time arrivals
            present_days = len([r for r in attendance_records if r['check_in']])
            on_time_days = 0
            
            for record in attendance_records:
                if record['check_in']:
                    try:
                        check_in_time = datetime.strptime(record['check_in'].split('T')[1][:8], '%H:%M:%S').time()
                        # Consider on-time if check-in is before 9:00 AM
                        if check_in_time <= datetime.strptime('09:00:00', '%H:%M:%S').time():
                            on_time_days += 1
                    except (ValueError, IndexError):
                        # Skip invalid time formats
                        continue
            
            # Calculate attendance percentage
            attendance_percentage = (present_days / max(total_working_days, 1)) * 100
            punctuality_percentage = (on_time_days / max(present_days, 1)) * 100
            
            # Convert to 1-5 scale (weighted: 70% attendance, 30% punctuality)
            combined_score = (attendance_percentage * 0.7 + punctuality_percentage * 0.3) / 100 * 5
            
            return float(round(min(max(combined_score, 1.0), 5.0), 2))
            
        except Exception as e:
            logger.error(f"Error calculating attendance score from data: {e}")
            return 3.0

    def calculate_attendance_score(self, person_id: str, days: int = 90) -> float:
        """Calculate attendance score from attendance table"""
        try:
            # Get attendance records for the last 90 days
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            result = self.supabase.table('attendance').select('work_date, check_in, check_out').eq('person_id', person_id).gte('work_date', start_date).execute()
            
            attendance_records = result.data
            
            if not attendance_records:
                return 3.0  # Default score if no attendance data
            
            # Calculate working days (excluding weekends)
            total_working_days = 0
            current_date = start_date
            while current_date <= datetime.now().date():
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    total_working_days += 1
                current_date += timedelta(days=1)
            
            # Calculate present days and on-time arrivals
            present_days = len([r for r in attendance_records if r['check_in']])
            on_time_days = 0
            
            for record in attendance_records:
                if record['check_in']:
                    try:
                        check_in_time = datetime.strptime(record['check_in'].split('T')[1][:8], '%H:%M:%S').time()
                        # Consider on-time if check-in is before 9:00 AM
                        if check_in_time <= datetime.strptime('09:00:00', '%H:%M:%S').time():
                            on_time_days += 1
                    except (ValueError, IndexError):
                        # Skip invalid time formats
                        continue
            
            # Calculate attendance percentage
            attendance_percentage = (present_days / max(total_working_days, 1)) * 100
            punctuality_percentage = (on_time_days / max(present_days, 1)) * 100
            
            # Convert to 1-5 scale (weighted: 70% attendance, 30% punctuality)
            combined_score = (attendance_percentage * 0.7 + punctuality_percentage * 0.3) / 100 * 5
            
            return float(round(min(max(combined_score, 1.0), 5.0), 2))
            
        except Exception as e:
            logger.error(f"Error calculating attendance score: {e}")
            return 3.0

    # PERFORMANCE CALCULATION METHODS
    def calculate_performance_score(self, performance_data: Dict) -> float:
        """Calculate weighted performance score"""
        try:
            score = 0.0
            total_weight = 0.0
            
            for criterion, weight in self.performance_weights.items():
                if criterion == 'engagement':
                    # Handle both percentage and 1-5 scale
                    value = performance_data.get('engagement_percentage', 0)
                    if value > 5:  # It's a percentage
                        value = float(value) / 100 * 5
                    else:
                        value = float(performance_data.get('engagement', value or 0))
                else:
                    value = float(performance_data.get(criterion, 0))
                
                if value > 0:  # Only include non-zero values
                    score += value * weight
                    total_weight += weight
            
            return float(round(score / max(total_weight, 0.1), 2))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0

    def calculate_performance_score_from_criteria(self, criteria_scores: Dict, attendance_score: float, engagement_percentage: int) -> float:
        """Calculate performance score from individual criteria"""
        try:
            # Add attendance and engagement to criteria scores
            all_scores = criteria_scores.copy()
            all_scores['attendance_punctuality'] = float(attendance_score)
            all_scores['engagement'] = float((engagement_percentage or 80) / 100) * 5
            
            return self.calculate_performance_score(all_scores)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0

    # PERFORMANCE TIER AND DISTRIBUTION METHODS
    def get_performance_tier(self, score: float) -> str:
        """Get performance tier based on score"""
        if score >= 4.5:
            return "Exceptional"
        elif score >= 4.0:
            return "Exceeds Expectations"
        elif score >= 3.5:
            return "Meets Expectations"
        elif score >= 3.0:
            return "Needs Improvement"
        else:
            return "Unsatisfactory"
    
    def get_criterion_tier(self, score: float) -> str:
        """Get tier for individual criterion"""
        if score >= 4.5:
            return "Outstanding"
        elif score >= 4.0:
            return "Strong"
        elif score >= 3.5:
            return "Satisfactory"
        elif score >= 3.0:
            return "Developing"
        else:
            return "Needs Focus"
    
    def get_performance_distribution(self, employees: List[Dict]) -> Dict:
        """Get performance distribution statistics"""
        tiers = {}
        total = len(employees)
        
        for emp in employees:
            tier = emp['performance_tier']
            tiers[tier] = tiers.get(tier, 0) + 1
        
        # Convert to percentages
        distribution = {}
        for tier, count in tiers.items():
            distribution[tier] = {
                'count': count,
                'percentage': round((count / max(total, 1)) * 100, 1)
            }
        
        return distribution

    # QUARTERLY RANKINGS AND ANALYSIS
    def get_quarterly_rankings(self, quarter: str = None, year: int = None) -> Dict:
        """Get quarterly employee rankings"""
        try:
            if not quarter:
                current_date = datetime.now()
                quarter = f"Q{((current_date.month - 1) // 3) + 1}"
            if not year:
                year = datetime.now().year
            
            employees = self.get_employee_performance_data()
            
            if not employees:
                return {
                    'error': 'No employee data available. Please check your database connection and ensure employees exist.',
                    'period': f"{quarter} {year}",
                    'total_employees': 0,
                    'overall_rankings': [],
                    'department_rankings': {},
                    'performance_distribution': {},
                    'last_updated': datetime.now().isoformat()
                }
            
            # Calculate performance scores and sort
            for emp in employees:
                emp['calculated_score'] = self.calculate_performance_score(emp)
            
            # Sort by performance score (descending)
            ranked_employees = sorted(employees, key=lambda x: x['calculated_score'], reverse=True)
            
            # Add ranking
            for i, emp in enumerate(ranked_employees):
                emp['rank'] = i + 1
                emp['performance_tier'] = self.get_performance_tier(emp['calculated_score'])
            
            # Department-wise rankings
            dept_rankings = {}
            for emp in ranked_employees:
                dept = emp['department']
                if dept not in dept_rankings:
                    dept_rankings[dept] = []
                dept_rankings[dept].append(emp)
            
            return {
                'period': f"{quarter} {year}",
                'total_employees': len(ranked_employees),
                'overall_rankings': ranked_employees,
                'department_rankings': dept_rankings,
                'performance_distribution': self.get_performance_distribution(ranked_employees),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quarterly rankings: {e}")
            return {
                'error': str(e),
                'period': f"{quarter} {year}",
                'total_employees': 0,
                'overall_rankings': [],
                'department_rankings': {},
                'performance_distribution': {},
                'last_updated': datetime.now().isoformat()
            }

    # DETAILED EMPLOYEE ANALYSIS
    def get_employee_detail(self, employee_id: str) -> Dict:
        """Get detailed employee performance profile"""
        try:
            employees = self.get_employee_performance_data()

            if not employees:
                return {'error': 'No employee data available. Please check your database connection.'}

            employee = next((emp for emp in employees if emp['employee_id'] == employee_id), None)

            if not employee:
                return {'error': f'Employee {employee_id} not found'}

            # Add calculated metrics
            employee['calculated_score'] = self.calculate_performance_score(employee)
            employee['performance_tier'] = self.get_performance_tier(employee['calculated_score'])

            # Get performance history
            performance_history = self.get_performance_history(employee_id)

            # Get peer comparison
            peer_comparison = self.get_peer_comparison(employee)

            return {
                'employee_profile': employee,
                'performance_breakdown': self.get_performance_breakdown(employee),
                'performance_history': performance_history,
                'peer_comparison': peer_comparison,
                'improvement_areas': self.get_improvement_areas(employee),
                'strengths': self.get_strengths(employee),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting employee detail: {e}")
            return {'error': str(e)}

    def calculate_attendance_score(self, person_id: str, days: int = 90) -> float:
        """Calculate attendance score from attendance table"""
        try:
            # Get attendance records for the last 90 days
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            result = self.supabase.table('attendance').select('work_date, check_in, check_out').eq('person_id', person_id).gte('work_date', start_date).execute()
            
            attendance_records = result.data
            
            if not attendance_records:
                return 3.0  # Default score if no attendance data
            
            # Calculate working days (excluding weekends)
            total_working_days = 0
            current_date = start_date
            while current_date <= datetime.now().date():
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    total_working_days += 1
                current_date += timedelta(days=1)
            
            # Calculate present days and on-time arrivals
            present_days = len([r for r in attendance_records if r['check_in']])
            on_time_days = 0
            
            for record in attendance_records:
                if record['check_in']:
                    try:
                        check_in_time = datetime.strptime(record['check_in'].split('T')[1][:8], '%H:%M:%S').time()
                        # Consider on-time if check-in is before 9:00 AM
                        if check_in_time <= datetime.strptime('09:00:00', '%H:%M:%S').time():
                            on_time_days += 1
                    except (ValueError, IndexError):
                        # Skip invalid time formats
                        continue
            
            # Calculate attendance percentage
            attendance_percentage = (present_days / max(total_working_days, 1)) * 100
            punctuality_percentage = (on_time_days / max(present_days, 1)) * 100
            
            # Convert to 1-5 scale (weighted: 70% attendance, 30% punctuality)
            combined_score = (attendance_percentage * 0.7 + punctuality_percentage * 0.3) / 100 * 5
            
            return float(round(min(max(combined_score, 1.0), 5.0), 2))
            
        except Exception as e:
            logger.error(f"Error calculating attendance score: {e}")
            return 3.0

    def calculate_performance_score_from_criteria(self, criteria_scores: Dict, attendance_score: float, engagement_percentage: int) -> float:
        """Calculate performance score from individual criteria"""
        try:
            # Add attendance and engagement to criteria scores
            all_scores = criteria_scores.copy()
            all_scores['attendance_punctuality'] = float(attendance_score)
            all_scores['engagement'] = float((engagement_percentage or 80) / 100) * 5
            
            return self.calculate_performance_score(all_scores)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0

    def calculate_performance_score(self, performance_data: Dict) -> float:
        """Calculate weighted performance score"""
        try:
            score = 0.0
            total_weight = 0.0
            
            for criterion, weight in self.performance_weights.items():
                if criterion == 'engagement':
                    # Handle both percentage and 1-5 scale
                    value = performance_data.get('engagement_percentage', 0)
                    if value > 5:  # It's a percentage
                        value = float(value) / 100 * 5
                    else:
                        value = float(performance_data.get('engagement', value or 0))
                else:
                    value = float(performance_data.get(criterion, 0))
                
                if value > 0:  # Only include non-zero values
                    score += value * weight
                    total_weight += weight
            
            return float(round(score / max(total_weight, 0.1), 2))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def get_quarterly_rankings(self, quarter: str = None, year: int = None) -> Dict:
        """Get quarterly employee rankings"""
        try:
            if not quarter:
                current_date = datetime.now()
                quarter = f"Q{((current_date.month - 1) // 3) + 1}"
            if not year:
                year = datetime.now().year
            
            employees = self.get_employee_performance_data()
            
            if not employees:
                return {
                    'error': 'No employee data available. Please check your database connection and ensure employees exist.',
                    'period': f"{quarter} {year}",
                    'total_employees': 0,
                    'overall_rankings': [],
                    'department_rankings': {},
                    'performance_distribution': {},
                    'last_updated': datetime.now().isoformat()
                }
            
            # Calculate performance scores and sort
            for emp in employees:
                emp['calculated_score'] = self.calculate_performance_score(emp)
            
            # Sort by performance score (descending)
            ranked_employees = sorted(employees, key=lambda x: x['calculated_score'], reverse=True)
            
            # Add ranking
            for i, emp in enumerate(ranked_employees):
                emp['rank'] = i + 1
                emp['performance_tier'] = self.get_performance_tier(emp['calculated_score'])
            
            # Department-wise rankings
            dept_rankings = {}
            for emp in ranked_employees:
                dept = emp['department']
                if dept not in dept_rankings:
                    dept_rankings[dept] = []
                dept_rankings[dept].append(emp)
            
            return {
                'period': f"{quarter} {year}",
                'total_employees': len(ranked_employees),
                'overall_rankings': ranked_employees,
                'department_rankings': dept_rankings,
                'performance_distribution': self.get_performance_distribution(ranked_employees),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quarterly rankings: {e}")
            return {
                'error': str(e),
                'period': f"{quarter} {year}",
                'total_employees': 0,
                'overall_rankings': [],
                'department_rankings': {},
                'performance_distribution': {},
                'last_updated': datetime.now().isoformat()
            }

    def get_employee_detail(self, employee_id: str) -> Dict:
        """Get detailed employee performance profile"""
        try:
            employees = self.get_employee_performance_data()
            
            if not employees:
                return {'error': 'No employee data available. Please check your database connection.'}
            
            employee = next((emp for emp in employees if emp['employee_id'] == employee_id), None)
            
            if not employee:
                return {'error': f'Employee {employee_id} not found'}
            
            # Add calculated metrics
            employee['calculated_score'] = self.calculate_performance_score(employee)
            employee['performance_tier'] = self.get_performance_tier(employee['calculated_score'])
            
            # Get performance history
            performance_history = self.get_performance_history(employee_id)
            
            # Get peer comparison
            peer_comparison = self.get_peer_comparison(employee)
            
            return {
                'employee_profile': employee,
                'performance_breakdown': self.get_performance_breakdown(employee),
                'performance_history': performance_history,
                'peer_comparison': peer_comparison,
                'improvement_areas': self.get_improvement_areas(employee),
                'strengths': self.get_strengths(employee),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting employee detail: {e}")
            return {'error': str(e)}
            
        except Exception as e:
            logger.error(f"Error getting employee detail: {e}")
            return {'error': str(e)}

    def get_performance_breakdown(self, employee: Dict) -> Dict:
        """Get detailed performance breakdown by criteria"""
        breakdown = {}
        
        for criterion, weight in self.performance_weights.items():
            if criterion == 'engagement':
                value = (employee.get('engagement_percentage', 0) / 100) * 5
                display_value = f"{employee.get('engagement_percentage', 0)}%"
            else:
                value = employee.get(criterion, 0)
                display_value = f"{value}/5"
            
            breakdown[criterion] = {
                'score': value,
                'display_value': display_value,
                'weight_percentage': weight * 100,
                'weighted_contribution': value * weight,
                'tier': self.get_criterion_tier(value)
            }
        
        return breakdown
    
    def get_criterion_tier(self, score: float) -> str:
        """Get tier for individual criterion"""
        if score >= 4.5:
            return "Outstanding"
        elif score >= 4.0:
            return "Strong"
        elif score >= 3.5:
            return "Satisfactory"
        elif score >= 3.0:
            return "Developing"
        else:
            return "Needs Focus"
    
    def get_performance_tier(self, score: float) -> str:
        """Get performance tier based on score"""
        if score >= 4.5:
            return "Exceptional"
        elif score >= 4.0:
            return "Exceeds Expectations"
        elif score >= 3.5:
            return "Meets Expectations"
        elif score >= 3.0:
            return "Needs Improvement"
        else:
            return "Unsatisfactory"
    
    def get_performance_distribution(self, employees: List[Dict]) -> Dict:
        """Get performance distribution statistics"""
        tiers = {}
        total = len(employees)
        
        for emp in employees:
            tier = emp['performance_tier']
            tiers[tier] = tiers.get(tier, 0) + 1
        
        # Convert to percentages
        distribution = {}
        for tier, count in tiers.items():
            distribution[tier] = {
                'count': count,
                'percentage': round((count / max(total, 1)) * 100, 1)
            }
        
        return distribution

    def get_performance_history(self, employee_id: str) -> List[Dict]:
        """Get performance history from quarterly summaries"""
        try:
            # Get person_id
            employees = self.get_employee_performance_data()
            employee = next((emp for emp in employees if emp['employee_id'] == employee_id), None)
            
            if not employee:
                return []
            
            person_id = employee['person_id']
            
            # Get quarterly performance summaries
            result = self.supabase.table('quarterly_performance_summary').select(
                'quarter, year, overall_score, company_rank'
            ).eq('person_id', person_id).order('year', desc=True).order('quarter', desc=True).limit(8).execute()
            
            history = []
            for record in result.data:
                history.append({
                    'period': f"{record['quarter']} {record['year']}",
                    'score': record['overall_score'],
                    'rank': record['company_rank'] or 0
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return []
    
    def get_peer_comparison(self, employee: Dict) -> Dict:
        """Get comparison with department peers"""
        employees = self.get_employee_performance_data()
        department_peers = [emp for emp in employees if emp['department'] == employee['department']]
        
        if len(department_peers) <= 1:
            return {'message': 'No department peers for comparison'}
        
        peer_scores = [self.calculate_performance_score(emp) for emp in department_peers]
        employee_score = self.calculate_performance_score(employee)
        
        return {
            'department_average': round(sum(peer_scores) / len(peer_scores), 2),
            'employee_score': employee_score,
            'percentile': self.calculate_percentile(employee_score, peer_scores),
            'department_rank': sorted(peer_scores, reverse=True).index(employee_score) + 1,
            'total_peers': len(department_peers)
        }
    
    def calculate_percentile(self, score: float, all_scores: List[float]) -> int:
        """Calculate percentile ranking"""
        below_score = len([s for s in all_scores if s < score])
        return round((below_score / len(all_scores)) * 100)
    
    def get_improvement_areas(self, employee: Dict) -> List[Dict]:
        """Identify areas for improvement"""
        areas = []
        
        for criterion, weight in self.performance_weights.items():
            if criterion == 'engagement':
                score = (employee.get('engagement_percentage', 0) / 100) * 5
            else:
                score = employee.get(criterion, 0)
            
            if score < 3.5:  # Below satisfactory
                areas.append({
                    'criterion': criterion.replace('_', ' ').title(),
                    'current_score': score,
                    'target_score': 4.0,
                    'priority': 'High' if score < 3.0 else 'Medium',
                    'weight': weight * 100
                })
        
        return sorted(areas, key=lambda x: x['current_score'])
    
    def get_strengths(self, employee: Dict) -> List[Dict]:
        """Identify employee strengths"""
        strengths = []
        
        for criterion, weight in self.performance_weights.items():
            if criterion == 'engagement':
                score = (employee.get('engagement_percentage', 0) / 100) * 5
            else:
                score = employee.get(criterion, 0)
            
            if score >= 4.0:  # Strong performance
                strengths.append({
                    'criterion': criterion.replace('_', ' ').title(),
                    'score': score,
                    'tier': self.get_criterion_tier(score),
                    'weight': weight * 100
                })
        
        return sorted(strengths, key=lambda x: x['score'], reverse=True)
    
    def update_employee_scores(self, employee_id: str, scores: Dict) -> Dict:
        """Update employee performance scores in database"""
        try:
            # Get current active appraisal cycle
            cycle_result = self.supabase.table('appraisal_cycle').select('*').order('created_at', desc=True).limit(1).execute()
            
            if not cycle_result.data:
                return {'error': 'No active appraisal cycle found'}
            
            cycle_id = cycle_result.data[0]['id']
            
            # Get person_id from employee_id (assuming we can map this)
            # For now, we'll need to find the person by employee details
            employees = self.get_employee_performance_data()
            employee = next((emp for emp in employees if emp['employee_id'] == employee_id), None)
            
            if not employee:
                return {'error': f'Employee {employee_id} not found'}
            
            person_id = employee['person_id']
            
            # Validate scores (1-5 Likert scale for most, 0-100 for engagement)
            criteria_scores = {}
            for criterion, score in scores.items():
                if criterion == 'engagement_percentage':
                    if not (0 <= score <= 100):
                        return {'error': f'Invalid engagement percentage: must be between 0 and 100'}
                    criteria_scores['engagement'] = score
                elif criterion in ['job_knowledge', 'quality_of_work', 'productivity', 'communication', 'initiative']:
                    if not (1 <= score <= 5):
                        return {'error': f'Invalid score for {criterion}: must be between 1 and 5'}
                    criteria_scores[criterion] = score
                # Skip attendance_punctuality as it's calculated from attendance table
            
            # Calculate new performance score
            all_scores = criteria_scores.copy()
            all_scores['attendance_punctuality'] = self.calculate_attendance_score(person_id)
            all_scores['engagement_percentage'] = scores.get('engagement_percentage', 80)
            
            new_score = self.calculate_performance_score(all_scores)
            performance_tier = self.get_performance_tier(new_score)
            
            # Prepare data for upsert
            performance_data = {
                'person_id': person_id,
                'appraisal_cycle_id': cycle_id,
                'criteria_scores': criteria_scores,
                'overall_score': new_score,
                'performance_tier': performance_tier,
                'engagement_percentage': scores.get('engagement_percentage', 80),
                'remarks': scores.get('remarks', ''),
                'last_review_date': datetime.now().date().isoformat(),
                'next_review_date': (datetime.now().date() + timedelta(days=90)).isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Upsert employee performance record
            result = self.supabase.table('employee_performance_record').upsert(
                performance_data, 
                on_conflict='person_id,appraisal_cycle_id'
            ).execute()
            
            if result.data:
                return {
                    'success': True,
                    'employee_id': employee_id,
                    'updated_scores': scores,
                    'new_performance_score': new_score,
                    'performance_tier': performance_tier,
                    'updated_at': datetime.now().isoformat()
                }
            else:
                return {'error': 'Failed to update performance record'}
            
        except Exception as e:
            logger.error(f"Error updating employee scores: {e}")
            return {'error': str(e)}
    
    def generate_quarterly_summary(self, quarter: str, year: int) -> Dict:
        """Generate and cache quarterly performance summary"""
        try:
            employees = self.get_employee_performance_data()
            
            if not employees:
                return {'error': 'No employee performance data available'}
            
            # Calculate and rank employees
            for emp in employees:
                emp['calculated_score'] = emp['performance_score']
                emp['performance_tier'] = self.get_performance_tier(emp['calculated_score'])
            
            # Sort by performance score
            ranked_employees = sorted(employees, key=lambda x: x['calculated_score'], reverse=True)
            
            # Assign ranks and save to quarterly summary
            for i, emp in enumerate(ranked_employees):
                emp['rank'] = i + 1
                
                # Save to quarterly summary table
                summary_data = {
                    'quarter': quarter,
                    'year': year,
                    'person_id': emp['person_id'],
                    'overall_score': emp['calculated_score'],
                    'company_rank': emp['rank'],
                    'performance_tier': emp['performance_tier']
                }
                
                # Upsert quarterly summary
                self.supabase.table('quarterly_performance_summary').upsert(
                    summary_data,
                    on_conflict='person_id,quarter,year'
                ).execute()
            
            return {
                'success': True,
                'period': f"{quarter} {year}",
                'employees_processed': len(ranked_employees),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating quarterly summary: {e}")
            return {'error': str(e)}
    
    def get_employee_performance_data_cached(self) -> List[Dict]:
        """Get employee performance data with caching"""
        return self.get_cached_employee_performance_data(self)
    
    # Add caching to prevent repeated calls
    # @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_cached_employee_performance_data(_self) -> List[Dict]:
        """Cached version of employee performance data"""
        return _self.get_employee_performance_data()
