# -*- coding: utf-8 -*-
"""
HR Dashboard Component for Live Data Visualization
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from hr_analytics import HRAnalyticsService
from performance_analytics import PerformanceAnalyticsService

class HRDashboard:
    """Live HR Dashboard with real-time analytics"""
    
    _instance = None
    _initialized = False

    def __new__(cls):
        """Implement singleton pattern to prevent re-initialization"""
        if cls._instance is None:
            cls._instance = super(HRDashboard, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize dashboard with analytics service - only once"""
        if not self._initialized:
            self.analytics = HRAnalyticsService()
            self.performance_analytics = PerformanceAnalyticsService()
            self.logger = logging.getLogger(__name__)
            HRDashboard._initialized = True
    
    def render_dashboard(self):
        """Render the complete HR dashboard"""
        st.markdown("## 📊 Live HR Dashboard")
        st.markdown("*Real-time data from your HR system*")
        
        # Initialize session state for data caching
        if 'dashboard_last_refresh' not in st.session_state:
            st.session_state.dashboard_last_refresh = datetime.now()
            st.session_state.dashboard_data = None
            st.session_state.employee_data = None
        
        # Refresh button
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 Refresh Data", width='content'):
                # Clear session state cache
                if 'dashboard_data' in st.session_state:
                    del st.session_state.dashboard_data
                if 'employee_data' in st.session_state:
                    del st.session_state.employee_data
                st.session_state.dashboard_last_refresh = datetime.now()
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            # Remove auto-refresh to prevent unnecessary queries
            st.write("🕒 Last updated:")
            st.write(st.session_state.dashboard_last_refresh.strftime("%H:%M:%S"))
        
        # Dashboard tabs
        tab1, tab2, tab3 = st.tabs(["📈 Analytics Overview", "🏆 Quarterly Index", "👤 Employee Profiles"])
        
        with tab1:
            # Only load data if not in session state or expired
            if (st.session_state.dashboard_data is None or 
                (datetime.now() - st.session_state.dashboard_last_refresh).seconds > 300):  # 5 minutes
                
                with st.spinner("Loading dashboard data..."):
                    st.session_state.dashboard_data = self.analytics.get_hr_dashboard_summary()
                    st.session_state.dashboard_last_refresh = datetime.now()
            
            dashboard_data = st.session_state.dashboard_data
            
            if 'error' in dashboard_data:
                st.error(f"❌ Error loading dashboard: {dashboard_data['error']}")
                return
            
            # Render sections
            self.render_key_metrics(dashboard_data)
            self.render_headcount_section(dashboard_data['headcount'])
            self.render_attrition_section(dashboard_data['attrition'])
            self.render_alerts_section(dashboard_data)
            self.render_appraisal_section(dashboard_data.get('appraisal_status'))
        
        with tab2:
            self.render_quarterly_index()
        
        with tab3:
            self.render_employee_profiles()

    def get_cached_employee_performance_data(self) -> List[Dict]:
        """Get employee data from session state or database"""
        # Check session state first
        if (st.session_state.employee_data is None or 
            (datetime.now() - st.session_state.dashboard_last_refresh).seconds > 300):  # 5 minutes
            
            st.session_state.employee_data = self.performance_analytics.get_employee_performance_data()
            st.session_state.dashboard_last_refresh = datetime.now()
        
        return st.session_state.employee_data

    def render_key_metrics(self, data):
        """Render key metrics cards"""
        st.markdown("### 🎯 Key Metrics")
        
        summary = data.get('summary', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_employees = summary.get('total_employees', 0)
            st.metric(
                label="👥 Total Employees",
                value=f"{total_employees}",
                help="Current active headcount"
            )
        
        with col2:
            attrition_rate = summary.get('attrition_rate', 0)
            st.metric(
                label="📈 Attrition Rate",
                value=f"{attrition_rate}%",
                delta=f"Last 3 months",
                help="Employee departure rate"
            )
        
        with col3:
            appraisal_completion = summary.get('appraisal_completion', 0)
            st.metric(
                label="🎯 Appraisal Progress",
                value=f"{appraisal_completion}%",
                help="Current cycle completion rate"
            )
        
        with col4:
            total_alerts = summary.get('total_alerts', 0)
            alert_color = "🔴" if total_alerts > 5 else "🟡" if total_alerts > 0 else "🟢"
            st.metric(
                label=f"{alert_color} Active Alerts",
                value=f"{total_alerts}",
                help="Probation + Contract expiry alerts"
            )
    
    def render_headcount_section(self, headcount_data):
        """Render headcount visualization"""
        st.markdown("---")
        st.markdown("### 👥 Headcount Analysis")
        
        if 'error' in headcount_data:
            st.error(f"Error loading headcount data: {headcount_data['error']}")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Department breakdown pie chart
            dept_data = headcount_data.get('by_department', {})
            if dept_data:
                fig_dept = px.pie(
                    values=list(dept_data.values()),
                    names=list(dept_data.keys()),
                    title="Employees by Department"
                )
                fig_dept.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_dept, use_container_width=True)
        
        with col2:
            # Role breakdown bar chart
            role_data = headcount_data.get('by_role', {})
            if role_data:
                fig_role = px.bar(
                    x=list(role_data.keys()),
                    y=list(role_data.values()),
                    title="Employees by Role",
                    labels={'x': 'Role', 'y': 'Count'}
                )
                st.plotly_chart(fig_role, use_container_width=True)
    
    def render_attrition_section(self, attrition_data):
        """Render attrition analysis"""
        st.markdown("---")
        st.markdown("### 📈 Attrition Analysis")
        
        if 'error' in attrition_data:
            st.error(f"Error loading attrition data: {attrition_data['error']}")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Attrition by department
            dept_attrition = attrition_data.get('by_department', {})
            if dept_attrition:
                fig_attrition = px.bar(
                    x=list(dept_attrition.keys()),
                    y=list(dept_attrition.values()),
                    title="Departures by Department (Last 12 months)",
                    labels={'x': 'Department', 'y': 'Departures'}
                )
                st.plotly_chart(fig_attrition, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Attrition Summary")
            
            total_departures = attrition_data.get('total_terminations', 0)
            attrition_rate = attrition_data.get('attrition_rate_percent', 0)
            period = attrition_data.get('period_months', 12)
            
            st.info(f"""
            **Period:** Last {period} months  
            **Total Departures:** {total_departures}  
            **Attrition Rate:** {attrition_rate}%
            """)
    
    def render_alerts_section(self, data):
        """Render alerts and notifications"""
        st.markdown("---")
        st.markdown("### 🚨 Active Alerts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⏰ Probation Alerts")
            probation_data = data.get('probation_alerts', {})
            
            if 'error' in probation_data:
                st.error("Error loading probation data")
            else:
                total_alerts = probation_data.get('total_alerts', 0)
                upcoming = len(probation_data.get('upcoming_reviews', []))
                overdue = len(probation_data.get('overdue_reviews', []))
                
                if total_alerts == 0:
                    st.success("✅ No probation alerts")
                else:
                    st.warning(f"⚠️ {total_alerts} probation alerts")
                    st.write(f"• **Upcoming:** {upcoming} reviews")
                    st.write(f"• **Overdue:** {overdue} reviews")
                
                if st.button("View Details", key="probation_details"):
                    self.show_probation_details(probation_data)
        
        with col2:
            st.markdown("#### 📋 Contract Alerts")
            contract_data = data.get('contract_alerts', {})
            
            if 'error' in contract_data:
                st.error("Error loading contract data")
            else:
                expiring = contract_data.get('total_expiring', 0)
                
                if expiring == 0:
                    st.success("✅ No contract alerts")
                else:
                    st.warning(f"⚠️ {expiring} contracts expiring soon")
                
                if st.button("View Details", key="contract_details"):
                    self.show_contract_details(contract_data)
    
    def render_appraisal_section(self, appraisal_data):
        """Render appraisal progress"""
        st.markdown("---")
        st.markdown("### 🎯 Appraisal Progress")
        
        if not appraisal_data or 'error' in appraisal_data:
            st.info("📋 No active appraisal cycle or data unavailable")
            return
        
        if 'message' in appraisal_data:
            st.info(f"📋 {appraisal_data['message']}")
            return
        
        cycle_info = appraisal_data.get('cycle_info', {})
        completion_stats = appraisal_data.get('completion_stats', {})
        
        # Progress bar
        completion_rate = completion_stats.get('completion_rate_percent', 0)
        st.progress(completion_rate / 100)
        st.write(f"**{cycle_info.get('name', 'Current Cycle')}:** {completion_rate}% complete")
        
        col1, col2 = st.columns(2)
        
        with col1:
            completed = completion_stats.get('completed_appraisals', 0)
            total = completion_stats.get('total_appraisals', 0)
            pending = completion_stats.get('pending_appraisals', 0)
            
            st.metric("✅ Completed", f"{completed}/{total}")
            st.metric("⏳ Pending", pending)
        
        with col2:
            end_date = cycle_info.get('end_date')
            is_overdue = cycle_info.get('is_overdue', False)
            
            if is_overdue:
                st.error(f"🚨 Cycle overdue (ended {end_date})")
            else:
                st.info(f"📅 Cycle ends: {end_date}")
        
        # Department progress
        dept_data = appraisal_data.get('by_department', {})
        if dept_data:
            st.markdown("#### 📊 Progress by Department")
            
            dept_names = list(dept_data.keys())
            completion_rates = [dept_data[dept]['completion_rate'] for dept in dept_names]
            
            fig_progress = px.bar(
                x=dept_names,
                y=completion_rates,
                title="Appraisal Completion by Department",
                labels={'x': 'Department', 'y': 'Completion Rate (%)'}
            )
            fig_progress.update_layout(yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_progress, use_container_width=True)
    
    def show_probation_details(self, probation_data):
        """Show detailed probation information"""
        with st.expander("👥 Probation Review Details", expanded=True):
            upcoming = probation_data.get('upcoming_reviews', [])
            overdue = probation_data.get('overdue_reviews', [])
            
            if overdue:
                st.markdown("#### 🚨 Overdue Reviews")
                for review in overdue:
                    days_overdue = abs(review.get('days_until_end', 0))
                    st.error(f"**{review.get('name', 'Unknown')}** - {days_overdue} days overdue")
            
            if upcoming:
                st.markdown("#### ⏳ Upcoming Reviews")
                for review in upcoming:
                    days_remaining = review.get('days_until_end', 0)
                    st.warning(f"**{review.get('name', 'Unknown')}** - {days_remaining} days remaining")
    
    def show_contract_details(self, contract_data):
        """Show detailed contract information"""
        with st.expander("📋 Contract Expiry Details", expanded=True):
            contracts = contract_data.get('expiring_contracts', [])
            
            if contracts:
                for contract in contracts:
                    name = contract.get('name', 'Unknown')
                    days = contract.get('days_until_expiry', 0)
                    contract_type = contract.get('contract_type', 'Unknown')
                    
                    if days <= 7:
                        st.error(f"**{name}** ({contract_type}) - {days} days remaining")
                    else:
                        st.warning(f"**{name}** ({contract_type}) - {days} days remaining")
    
    def render_quarterly_index(self):
        """Render quarterly organizational index - OPTIMIZED"""
        st.markdown("### 🏆 Quarterly Organizational Index")
        st.markdown("*Employee performance rankings and analytics*")
        
        # Quarter selection
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"], index=3)
        with col2:
            year = st.selectbox("Year", [2024, 2025], index=1)
        
        # Get rankings data (now much faster with single query)
        with st.spinner("Loading performance data..."):
            rankings_data = self.performance_analytics.get_quarterly_rankings(quarter, year)
        
        if 'error' in rankings_data:
            st.error(f"❌ Error loading rankings: {rankings_data['error']}")
            st.info("💡 **Troubleshooting Tips:**")
            st.write("1. **Check Database Connection**: Ensure your Supabase connection is working")
            st.write("2. **Verify Employee Data**: Make sure you have active employees in your `people` table")
            st.write("3. **Run Database Migrations**: Execute the performance analytics schema setup")
            st.write("4. **Check Logs**: Look at the console for detailed error messages")
            return
        
        if rankings_data['total_employees'] == 0:
            st.warning("⚠️ No employee performance data found")
            st.info("💡 **Next Steps:**")
            st.write("1. **Add Employees**: Ensure you have active employees in your database")
            st.write("2. **Create Appraisal Cycle**: Set up an active appraisal cycle")
            st.write("3. **Add Performance Records**: Use the 'Update Scores' feature to add performance ratings")
            return
        
        # Performance distribution
        self.render_performance_distribution(rankings_data['performance_distribution'])
        
        # Rankings table
        self.render_rankings_table(rankings_data['overall_rankings'])
        
        # Department comparison
        self.render_department_comparison(rankings_data['department_rankings'])
    
    def render_performance_distribution(self, distribution: Dict):
        """Render performance tier distribution"""
        st.markdown("#### 📊 Performance Distribution")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Pie chart
            if distribution:
                labels = list(distribution.keys())
                values = [data['count'] for data in distribution.values()]
                
                fig_pie = px.pie(
                    values=values,
                    names=labels,
                    title="Employee Performance Tiers"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Distribution stats
            st.markdown("##### 📈 Distribution Stats")
            for tier, data in distribution.items():
                count = data['count']
                percentage = data['percentage']
                
                # Color coding
                if tier == "Exceptional":
                    st.success(f"🌟 **{tier}**: {count} ({percentage}%)")
                elif tier == "Exceeds Expectations":
                    st.info(f"⭐ **{tier}**: {count} ({percentage}%)")
                elif tier == "Meets Expectations":
                    st.write(f"✅ **{tier}**: {count} ({percentage}%)")
                elif tier == "Needs Improvement":
                    st.warning(f"⚠️ **{tier}**: {count} ({percentage}%)")
                else:
                    st.error(f"❌ **{tier}**: {count} ({percentage}%)")
    
    def render_rankings_table(self, employees: List[Dict]):
        """Render employee rankings table"""
        st.markdown("#### 🏆 Employee Rankings")
        
        # Create DataFrame for display
        df_data = []
        for emp in employees:
            df_data.append({
                'Rank': emp.get('rank', 0),
                'Employee ID': emp.get('employee_id', ''),
                'Name': emp.get('full_name', ''),
                'Department': emp.get('department', ''),
                'Role': emp.get('role_position', ''),
                'Performance Score': emp.get('calculated_score', 0),
                'Tier': emp.get('performance_tier', ''),
                'Last Review': emp.get('last_review_date', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Only apply styling if we have data and the Tier column exists
        if not df.empty and 'Tier' in df.columns:
            # Add styling function - FIXED: Use .map instead of deprecated .applymap
            def highlight_tier(val):
                if val == "Exceptional":
                    return 'background-color: #d4edda; color: #155724'
                elif val == "Exceeds Expectations":
                    return 'background-color: #cce7ff; color: #004085'
                elif val == "Meets Expectations":
                    return 'background-color: #fff3cd; color: #856404'
                elif val == "Needs Improvement":
                    return 'background-color: #f8d7da; color: #721c24'
                else:
                    return 'background-color: #f5c6cb; color: #721c24'
            
            try:
                styled_df = df.style.map(highlight_tier, subset=['Tier'])
            except Exception as e:
                self.logger.warning(f"Error applying DataFrame styling: {e}")
                styled_df = df
        else:
            styled_df = df
        
        # Display with selection - FIXED: Use new width parameter
        try:
            selected_rows = st.dataframe(
                styled_df,
                width='stretch',  # Replace deprecated use_container_width
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Handle row selection
            if selected_rows and len(selected_rows.selection.rows) > 0:
                selected_idx = selected_rows.selection.rows[0]
                if selected_idx < len(employees):
                    selected_employee = employees[selected_idx]
                    st.session_state.selected_employee_id = selected_employee.get('employee_id')
                    st.rerun()
        except Exception as e:
            st.error(f"Error displaying rankings table: {e}")
            # Fallback to simple dataframe display
            st.dataframe(df, width='stretch', hide_index=True)
    
    def render_employee_profiles(self):
        """Render detailed employee profiles - OPTIMIZED"""
        st.markdown("### 👤 Employee Performance Profiles")
        
        # Use session state cached employee data
        employees = self.get_cached_employee_performance_data()
        
        if not employees:
            st.warning("⚠️ No employee data available")
            st.info("💡 **Setup Required:**")
            st.write("1. **Database Setup**: Ensure your database tables are created")
            st.write("2. **Add Employees**: Add employees to your `people` table")
            st.write("3. **Check Connection**: Verify your Supabase connection settings")
            return
        
        employee_options = {f"{emp['full_name']} ({emp['employee_id']})": emp['employee_id'] for emp in employees}
        
        # Check if employee was selected from rankings table
        if 'selected_employee_id' in st.session_state:
            selected_emp_id = st.session_state.selected_employee_id
            # Find the display name for this ID
            selected_display = next((k for k, v in employee_options.items() if v == selected_emp_id), None)
            if selected_display:
                default_index = list(employee_options.keys()).index(selected_display)
            else:
                default_index = 0
        else:
            default_index = 0
        
        selected_employee = st.selectbox(
            "Select Employee",
            options=list(employee_options.keys()),
            index=default_index,
            help="Click on an employee in the rankings table or select here"
        )
        
        if selected_employee:
            employee_id = employee_options[selected_employee]
            
            # Get detailed profile from cached data instead of querying database
            employee = next((emp for emp in employees if emp['employee_id'] == employee_id), None)
            
            if not employee:
                st.error("❌ Employee not found")
                return
            
            # Build profile data from cached employee data
            profile_data = self.build_profile_from_cache(employee, employees)
            self.render_employee_detail(profile_data)

    def build_profile_from_cache(self, employee: Dict, all_employees: List[Dict]) -> Dict:
        """Build profile data from cached employee data without additional queries"""
        # Add calculated metrics
        employee['calculated_score'] = self.performance_analytics.calculate_performance_score(employee)
        employee['performance_tier'] = self.performance_analytics.get_performance_tier(employee['calculated_score'])
        
        # Build performance breakdown
        performance_breakdown = self.performance_analytics.get_performance_breakdown(employee)
        
        # Get peer comparison from cached data
        department_peers = [emp for emp in all_employees if emp['department'] == employee['department']]
        
        if len(department_peers) <= 1:
            peer_comparison = {'message': 'No department peers for comparison'}
        else:
            peer_scores = [self.performance_analytics.calculate_performance_score(emp) for emp in department_peers]
            employee_score = self.performance_analytics.calculate_performance_score(employee)
            
            peer_comparison = {
                'department_average': round(sum(peer_scores) / len(peer_scores), 2),
                'employee_score': employee_score,
                'percentile': self.performance_analytics.calculate_percentile(employee_score, peer_scores),
                'department_rank': sorted(peer_scores, reverse=True).index(employee_score) + 1,
                'total_peers': len(department_peers)
            }
        
        # Get strengths and improvement areas
        strengths = self.performance_analytics.get_strengths(employee)
        improvement_areas = self.performance_analytics.get_improvement_areas(employee)
        
        return {
            'employee_profile': employee,
            'performance_breakdown': performance_breakdown,
            'performance_history': [],  # Empty for now to avoid additional queries
            'peer_comparison': peer_comparison,
            'improvement_areas': improvement_areas,
            'strengths': strengths,
            'last_updated': datetime.now().isoformat()
        }

    def render_employee_detail(self, profile_data: Dict):
        """Render detailed employee profile"""
        employee = profile_data['employee_profile']
        
        # Employee header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"## 👤 {employee['full_name']}")
            st.markdown(f"**{employee['role_position']}** | {employee['department']}")
        with col2:
            st.metric("Performance Score", employee['calculated_score'])
        with col3:
            tier = employee['performance_tier']
            if tier == "Exceptional":
                st.success(f"🌟 {tier}")
            elif tier == "Exceeds Expectations":
                st.info(f"⭐ {tier}")
            elif tier == "Meets Expectations":
                st.write(f"✅ {tier}")
            else:
                st.warning(f"⚠️ {tier}")
        
        # Employee details tabs
        detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs([
            "📊 Performance Breakdown", 
            "📈 Trends & History", 
            "🔍 Peer Comparison", 
            "✏️ Update Scores"
        ])
        
        with detail_tab1:
            self.render_performance_breakdown(profile_data['performance_breakdown'])
            
            col1, col2 = st.columns(2)
            with col1:
                if profile_data['strengths']:
                    st.markdown("#### 💪 Strengths")
                    for strength in profile_data['strengths']:
                        st.success(f"**{strength['criterion']}**: {strength['score']:.1f}/5 ({strength['tier']})")
            
            with col2:
                if profile_data['improvement_areas']:
                    st.markdown("#### 📈 Improvement Areas")
                    for area in profile_data['improvement_areas']:
                        priority_color = "🔴" if area['priority'] == 'High' else "🟡"
                        st.warning(f"{priority_color} **{area['criterion']}**: {area['current_score']:.1f}/5")
        
        with detail_tab2:
            self.render_performance_history(profile_data['performance_history'])
        
        with detail_tab3:
            self.render_peer_comparison(profile_data['peer_comparison'])
        
        with detail_tab4:
            self.render_score_update_form(employee['employee_id'], employee)
    
    def render_performance_breakdown(self, breakdown: Dict):
        """Render detailed performance breakdown"""
        st.markdown("#### 📊 Performance Criteria Breakdown")
        
        # Create radar chart data
        criteria = []
        scores = []
        weights = []
        
        for criterion, data in breakdown.items():
            criteria.append(criterion.replace('_', ' ').title())
            scores.append(data['score'])
            weights.append(data['weight_percentage'])
        
        # Radar chart
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=scores,
            theta=criteria,
            fill='toself',
            name='Performance Score',
            line_color='rgb(31, 119, 180)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            title="Performance Radar Chart",
            showlegend=True
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Detailed breakdown table
        breakdown_data = []
        for criterion, data in breakdown.items():
            breakdown_data.append({
                'Criterion': criterion.replace('_', ' ').title(),
                'Score': data['display_value'],
                'Weight': f"{data['weight_percentage']:.0f}%",
                'Contribution': f"{data['weighted_contribution']:.2f}",
                'Tier': data['tier']
            })
        
        df_breakdown = pd.DataFrame(breakdown_data)
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
    
    def render_performance_history(self, history: List[Dict]):
        """Render performance history trends"""
        st.markdown("#### 📈 Performance Trends")
        
        if not history:
            st.info("No historical performance data available")
            return
        
        # Line chart
        periods = [item['period'] for item in history]
        scores = [item['score'] for item in history]
        ranks = [item['rank'] for item in history]
        
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Scatter(
            x=periods,
            y=scores,
            mode='lines+markers',
            name='Performance Score',
            line=dict(color='rgb(31, 119, 180)', width=3),
            yaxis='y'
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=periods,
            y=ranks,
            mode='lines+markers',
            name='Rank',
            line=dict(color='rgb(255, 127, 14)', width=3),
            yaxis='y2'
        ))
        
        fig_trend.update_layout(
            title='Performance Score and Rank Trends',
            xaxis_title='Period',
            yaxis=dict(title='Performance Score', side='left'),
            yaxis2=dict(title='Rank', side='right', overlaying='y', autorange='reversed'),
            legend=dict(x=0, y=1)
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    def render_peer_comparison(self, comparison: Dict):
        """Render peer comparison"""
        st.markdown("#### 🔍 Peer Comparison")
        
        if 'message' in comparison:
            st.info(comparison['message'])
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Employee Score",
                comparison['employee_score'],
                delta=f"{comparison['employee_score'] - comparison['department_average']:.2f}"
            )
        
        with col2:
            st.metric("Department Average", comparison['department_average'])
        
        with col3:
            st.metric("Department Rank", f"{comparison['department_rank']}/{comparison['total_peers']}")
        
        # Percentile display
        percentile = comparison['percentile']
        if percentile >= 75:
            st.success(f"🎯 Top performer - {percentile}th percentile in department")
        elif percentile >= 50:
            st.info(f"📊 Above average - {percentile}th percentile in department")
        else:
            st.warning(f"📈 Below average - {percentile}th percentile in department")
    
    def render_score_update_form(self, employee_id: str, employee: Dict):
        """Render form to update employee scores"""
        st.markdown("#### ✏️ Update Performance Scores")
        st.markdown("*Use the Likert scale (1-5) to rate performance*")
        
        with st.form(f"update_scores_{employee_id}"):
            st.markdown("##### Performance Criteria")
            
            col1, col2 = st.columns(2)
            
            # Ensure all slider values are of matching types (int)
            current_job_knowledge = int(employee.get('job_knowledge', 3))
            current_quality = int(employee.get('quality_of_work', 3))
            current_productivity = int(employee.get('productivity', 3))
            current_communication = int(employee.get('communication', 3))
            current_initiative = int(employee.get('initiative', 3))
            current_attendance = int(employee.get('attendance_punctuality', 3))
            current_engagement = int(employee.get('engagement_percentage', 80))
            
            with col1:
                job_knowledge = st.slider("Job Knowledge", 
                                        min_value=1, max_value=5, value=current_job_knowledge, step=1,
                                        help="Technical skills and domain expertise")
                quality_of_work = st.slider("Quality of Work", 
                                          min_value=1, max_value=5, value=current_quality, step=1,
                                          help="Accuracy, thoroughness, and attention to detail")
                productivity = st.slider("Productivity", 
                                       min_value=1, max_value=5, value=current_productivity, step=1,
                                       help="Efficiency and output volume")
                communication = st.slider("Communication", 
                                        min_value=1, max_value=5, value=current_communication, step=1,
                                        help="Verbal, written, and interpersonal skills")
            
            with col2:
                initiative = st.slider("Initiative", 
                                     min_value=1, max_value=5, value=current_initiative, step=1,
                                     help="Proactiveness and self-motivation")
                attendance = st.slider("Attendance/Punctuality", 
                                     min_value=1, max_value=5, value=current_attendance, step=1,
                                     help="Reliability and time management")
                engagement = st.slider("Engagement %", 
                                     min_value=0, max_value=100, value=current_engagement, step=1,
                                     help="Overall engagement and participation")
            
            # Additional notes
            remarks = st.text_area("Remarks", employee.get('remarks', ''),
                                 help="Additional comments and observations")
            
            # Submit button
            submitted = st.form_submit_button("🔄 Update Scores", type="primary")
            
            if submitted:
                new_scores = {
                    'job_knowledge': job_knowledge,
                    'quality_of_work': quality_of_work,
                    'productivity': productivity,
                    'communication': communication,
                    'initiative': initiative,
                    'attendance_punctuality': attendance,
                    'engagement_percentage': engagement,
                    'remarks': remarks
                }
                
                result = self.performance_analytics.update_employee_scores(employee_id, new_scores)
                
                if result.get('success'):
                    st.success(f"✅ Scores updated successfully! New performance score: {result['new_performance_score']}")
                    st.cache_data.clear()  # Clear cache to refresh data
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Error updating scores: {result.get('error')}")
    
    def render_department_comparison(self, dept_rankings: Dict):
        """Render department performance comparison"""
        st.markdown("#### 🏢 Department Performance Comparison")
        
        # Calculate department averages
        dept_averages = {}
        for dept, employees in dept_rankings.items():
            scores = [emp['calculated_score'] for emp in employees]
            dept_averages[dept] = {
                'average_score': round(sum(scores) / len(scores), 2),
                'employee_count': len(employees),
                'top_performer': max(employees, key=lambda x: x['calculated_score']),
                'score_range': f"{min(scores):.2f} - {max(scores):.2f}"
            }
        
        # Bar chart
        dept_names = list(dept_averages.keys())
        avg_scores = [data['average_score'] for data in dept_averages.values()]
        
        fig_dept = px.bar(
            x=dept_names,
            y=avg_scores,
            title="Average Performance Score by Department",
            labels={'x': 'Department', 'y': 'Average Score'}
        )
        fig_dept.update_layout(yaxis=dict(range=[0, 5]))
        st.plotly_chart(fig_dept, use_container_width=True)
        
        # Department details
        for dept, data in dept_averages.items():
            with st.expander(f"📋 {dept} Department Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Average Score", data['average_score'])
                    st.metric("Employee Count", data['employee_count'])
                with col2:
                    st.write(f"**Score Range:** {data['score_range']}")
                    st.write(f"**Top Performer:** {data['top_performer']['full_name']} ({data['top_performer']['calculated_score']})")