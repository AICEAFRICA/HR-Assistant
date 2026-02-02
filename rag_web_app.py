# -*- coding: utf-8 -*-
"""
Role-based Streamlit web interface for HR RAG system with improved UI layout
- Employee View: Basic HR queries and self-service
- HR Personnel View: Advanced features, analytics, and management
"""
import streamlit as st
import os
from query_router import HRQueryRouter
from datetime import datetime, date
import json
from hr_dashboard import HRDashboard
import time

# Page config
st.set_page_config(
    page_title="HR Assistant - AI Powered",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
def initialize_session_state():
    """Initialize all session state variables"""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = "Employee"
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    if 'show_document_generator' not in st.session_state:
        st.session_state.show_document_generator = False
    
    if 'dashboard_last_refresh' not in st.session_state:
        st.session_state.dashboard_last_refresh = datetime.now()
    
    if 'dashboard_data' not in st.session_state:
        st.session_state.dashboard_data = None
    
    if 'employee_data' not in st.session_state:
        st.session_state.employee_data = None
    
    if 'show_leave_request' not in st.session_state:
        st.session_state.show_leave_request = False
    
    if 'show_my_leaves' not in st.session_state:
        st.session_state.show_my_leaves = False
    
    if 'show_leave_management' not in st.session_state:
        st.session_state.show_leave_management = False

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .role-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .sidebar-section {
        margin: 20px 0;
        padding: 15px 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .urgent-button {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

def init_query_router():
    """Initialize query router with caching"""
    if 'query_router' not in st.session_state:
        with st.spinner("🔧 Initializing HR Assistant..."):
            try:
                gemini_key = os.getenv("GEMINI_API_KEY")
                if not gemini_key:
                    st.error("❌ Gemini API key not found. Please check your environment variables.")
                    st.stop()
                
                st.session_state.query_router = HRQueryRouter(gemini_api_key=gemini_key)
                st.success("✅ HR Assistant initialized successfully!")
                
            except Exception as e:
                st.error(f"❌ Failed to initialize HR Assistant: {str(e)}")
                st.stop()
    
    return st.session_state.query_router

def display_response(response, show_metadata=False):
    """Display RAG response in a nice format"""
    
    # Main answer with better styling
    st.markdown("### 💬 Response")
    with st.container():
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #1f77b4;">
            {response['answer']}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Response metrics in a nice layout
    st.markdown("#### 📊 Response Quality")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence_color = "🟢" if response['confidence_score'] > 0.8 else "🟡" if response['confidence_score'] > 0.6 else "🔴"
        st.markdown(f"""
        <div class="metric-container">
            <strong>Confidence</strong><br>
            {confidence_color} {response['confidence_level']}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <strong>Score</strong><br>
            📈 {response['confidence_score']:.2f}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        sources_used = response.get('sources_used', len(response.get('chunks', [])))
        st.markdown(f"""
        <div class="metric-container">
            <strong>Sources</strong><br>
            📚 {sources_used}
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        coverage = response.get('coverage', 'Good')
        if isinstance(coverage, str):
            coverage_text = coverage.title()
        else:
            coverage_text = 'Good'
        st.markdown(f"""
        <div class="metric-container">
            <strong>Coverage</strong><br>
            📄 {coverage_text}
        </div>
        """, unsafe_allow_html=True)
    
    # Show query type information for HR Personnel
    if show_metadata and response.get('query_type'):
        st.markdown("---")
        st.markdown("#### 🔍 Query Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            query_type = response.get('query_type', 'unknown').replace('_', ' ').title()
            st.info(f"**Query Type:** {query_type}")
        with col2:
            data_type = response.get('data_type', 'unknown').replace('_', ' ').title()  
            st.info(f"**Data Type:** {data_type}")
    
    # Sources section (role-specific)
    if response.get('chunks') and len(response.get('chunks', [])) > 0:
        st.markdown("---")
        if st.session_state.user_role == "HR Personnel":
            st.markdown("#### 📚 Detailed Sources")
            for i, chunk in enumerate(response['chunks'], 1):
                with st.expander(f"📄 Source {i}: {chunk.get('article_title', 'Unknown Document')} (Relevance: {chunk.get('similarity', 0):.2f})"):
                    st.markdown(chunk.get('content', 'No content available'))
        else:
            st.markdown("#### 📚 Information Sources")
            doc_names = list(set(chunk.get('article_title', 'Unknown Document') for chunk in response['chunks']))
            for doc in doc_names:
                st.markdown(f"📋 {doc}")
    
    # Data query specific information
    if response.get('response_type', '').startswith('data_query'):
        st.markdown("---")
        st.markdown("#### 📊 Data Information")
        st.info("ℹ️ This information was retrieved from live HR database records.")
    
    # Technical metadata (HR Personnel only)
    if show_metadata and st.session_state.user_role == "HR Personnel":
        st.markdown("---")
        with st.expander("🔧 Technical Details"):
            metadata = {
                'query_type': response.get('query_type', 'unknown'),
                'data_type': response.get('data_type', 'unknown'), 
                'response_type': response.get('response_type', 'unknown'),
                'routing_metadata': response.get('routing_metadata', {}),
                'confidence_score': response.get('confidence_score', 0),
                'processing_method': 'Database Query' if response.get('query_type') == 'data_query' else 'Document RAG'
            }
            st.json(metadata)

def setup_sidebar():
    """Setup role-specific sidebar content"""
    
    with st.sidebar:
        # Role switcher at the top of sidebar
        st.markdown("## 🔄 Role Selection")
        role_options = ["Employee", "HR Personnel"]
        current_role = st.selectbox(
            "Select your role:",
            role_options,
            index=role_options.index(st.session_state.user_role),
            key="role_selector"
        )
        
        # Update role if changed
        if current_role != st.session_state.user_role:
            st.session_state.user_role = current_role
            st.session_state.chat_history = []  # Clear history on role change
            st.rerun()
        
        st.markdown("---")
        
        # Role-specific sidebar content
        if st.session_state.user_role == "Employee":
            return setup_employee_sidebar()
        else:
            return setup_hr_sidebar()

def setup_employee_sidebar():
    """Sidebar content for employees"""
    
    # Employee Self-Service Section
    st.markdown("## 👤 Employee Self-Service")
    with st.expander("🔍 What can I ask?", expanded=True):
        st.markdown("""
        • **Leave & Time Off** - Vacation, sick leave, PTO policies
                    
        • **Benefits** - Health insurance, retirement, perks
                    
        • **Policies** - Dress code, remote work, company rules 
                     
        • **Payroll** - Salary, deductions, tax information
                    
        • **Training** - Available courses, skill development
                    
        • **IT Support** - Equipment, software, troubleshooting
        """)
    
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    
    # Leave Management Section - NEW
    st.markdown("## 📝 Leave Management")
    if st.button("📅 Request Leave", use_container_width=True):
        st.session_state.show_leave_request = True
        st.rerun()
    
    if st.button("📋 My Leave Requests", use_container_width=True):
        st.session_state.show_my_leaves = True
        st.rerun()
    
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    
    # Need More Help Section
    st.markdown("## 📞 Need More Help?")
    with st.expander("📧 Contact Information"):
        st.markdown("""
        **HR Department:**
        • 📧 Email: hr@adanianlabs.io
        • 📱 Phone: (555) 123-4567
        • 💬 Teams: @HR-Support
        • 🕒 Hours: Mon-Fri 9AM-5PM
        
        **IT Support:**
        • 📧 Email: it-support@company.com
        • 📱 Phone: (555) 123-4568
        • 🎫 Ticket System: Available 24/7
        """)
    
    with st.expander("🆘 Emergency Contacts"):
        st.markdown("""
        **Security:** (555) 911-SAFE
        **Medical Emergency:** 911
        **Employee Assistance Program:** (555) 123-HELP
        """)
    
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    
    # Settings Section
    st.markdown("## ⚙️ Settings")
    show_sources = st.checkbox("Show information sources", value=True, help="Display which documents were used to answer your question")
    
    # Quick Actions
    st.markdown("## ⚡ Quick Actions")
    if st.button("📝 Request Time Off", use_container_width=True):
        st.session_state.current_query = "How do I request time off?"
        st.rerun()
    
    if st.button("💰 Check Benefits", use_container_width=True):
        st.session_state.current_query = "What benefits am I entitled to?"
        st.rerun()
    
    if st.button("👔 Dress Code Info", use_container_width=True):
        st.session_state.current_query = "What is the company dress code?"
        st.rerun()
    
    return show_sources, False  # show_sources, show_metadata

def setup_hr_sidebar():
    """Sidebar content for HR personnel"""
    
    # Advanced Features Section
    st.markdown("## 🏢 Advanced Features")
    with st.expander("🎯 HR Management Tools", expanded=True):
        st.markdown("""
        **📋 Policy Queries:**
        • Performance review procedures
        • Compliance requirements  
        • Employee handbook questions
        
        **📊 Live Data Queries:**
        • Current headcount analysis
        • Attrition rates and trends
        • Probation status alerts
        • Appraisal completion tracking
        • Contract expiry monitoring
        
        **📄 Document Generation:**
        • Offer letters and contracts
        • Termination letters
        • Experience certificates
        • Custom HR documents
        
        **🔍 Analytics:**
        • Query routing insights
        • Response quality metrics
        """)
    
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    
    # Quick Data Queries Section
    st.markdown("## 📊 Quick Data Queries")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 Headcount", use_container_width=True):
            st.session_state.current_query = "Show me current headcount breakdown"
            st.rerun()
        
        if st.button("📈 Attrition", use_container_width=True):
            st.session_state.current_query = "What is our attrition rate?"
            st.rerun()
    
    with col2:
        if st.button("⏰ Probation", use_container_width=True):
            st.session_state.current_query = "Show me probation status alerts"
            st.rerun()
        
        if st.button("🎯 Appraisals", use_container_width=True):
            st.session_state.current_query = "What's the appraisal completion status?"
            st.rerun()
    
    if st.button("📋 Dashboard Summary", use_container_width=True):
        st.session_state.current_query = "Give me an HR dashboard summary"
        st.rerun()
    
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    
    # System Info Section  
    st.markdown("## 📊 System Info")
    
    # Session Analytics
    if 'chat_history' in st.session_state and st.session_state.chat_history:
        st.markdown("### 📈 Session Analytics")
        total_queries = len(st.session_state.chat_history)
        avg_confidence = sum(chat['response']['confidence_score'] for chat in st.session_state.chat_history) / total_queries
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔍 Queries", total_queries)
        with col2:
            st.metric("✅ Avg Confidence", f"{avg_confidence:.2f}")
    else:
        st.info("💡 Query statistics will appear after you ask questions")
    
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    
    # Settings Section
    st.markdown("## ⚙️ Advanced Settings")
    show_sources = st.checkbox("Show detailed sources", value=True, help="Display full source content and relevance scores")
    show_metadata = st.checkbox("Show response metadata", value=True, help="Display technical response details and query routing info")
    
    # Advanced Options
    with st.expander("🔧 Advanced Options"):
        st.markdown("**Query Processing:**")
        enable_urgent = st.checkbox("Enable urgent query mode", value=True)
        auto_escalate = st.checkbox("Auto-escalate low confidence responses", value=False)
        
        st.markdown("**Analytics:**")
        track_queries = st.checkbox("Track query analytics", value=True)
        export_enabled = st.checkbox("Enable data export", value=True)
    
    # Quick HR Actions - REMOVED Leave Management from here
    st.markdown("## ⚡ Quick HR Actions")
    if st.button("👥 Employee Onboarding", use_container_width=True):
        st.session_state.current_query = "What is the complete employee onboarding process?"
        st.rerun()
    
    if st.button("📋 Performance Reviews", use_container_width=True):
        st.session_state.current_query = "What are the performance review procedures?"
        st.rerun()
    
    if st.button("📄 Generate Document", use_container_width=True):
        st.session_state.show_document_generator = True
        st.rerun()
    
    if st.button("⚖️ Compliance Check", use_container_width=True):
        st.session_state.current_query = "What are our current compliance requirements?"
        st.rerun()
    
    if st.button("📊 Generate Report", use_container_width=True):
        st.session_state.current_query = "How do I generate employee reports?"
        st.rerun()
    
    return show_sources, show_metadata

def get_role_specific_questions():
    """Get sample questions based on user role"""
    
    employee_questions = [
        "What is the company's leave policy?",
        "How do I request time off?",
        "What benefits am I entitled to?",
        "How many employees work here?",
        "What is the dress code policy?",
        "How do I access my payslip?",
        "What should I do if I'm sick?",
        "What training opportunities are available?"
    ]
    
    hr_questions = [
        "Show me current headcount breakdown",
        "What is our attrition rate this year?", 
        "Who needs probation reviews soon?",
        "What's the appraisal completion status?",
        "Any contract expiry alerts?",
        "How do we handle employee disciplinary actions?",
        "What is the recruitment and hiring process?",
        "Give me an HR dashboard summary"
    ]
    
    if st.session_state.user_role == "Employee":
        return employee_questions
    else:
        return hr_questions

def render_chat_interface():
    """Render the chat interface content"""
    
    # Get sidebar settings
    show_sources, show_metadata = setup_sidebar()
    
    st.markdown("---")
    
    # Main chat interface
    st.markdown("### 💭 Ask Your Question")
    
    # Query input form
    with st.form(key="query_form", clear_on_submit=True):
        placeholder_text = {
            "Employee": "e.g., How do I request vacation time? or How many employees do we have?",
            "HR Personnel": "e.g., Show me probation status alerts or What's our attrition rate?"
        }
        
        query = st.text_area(
            "Type your question here:",
            placeholder=placeholder_text[st.session_state.user_role],
            value=st.session_state.current_query,
            height=100
        )
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 6])
        
        with col1:
            ask_button = st.form_submit_button("🚀 Ask Question", type="primary", use_container_width=True)
        
        with col2:
            if st.session_state.user_role == "HR Personnel":
                urgent_button = st.form_submit_button("🚨 Urgent Query", type="secondary", use_container_width=True)
            else:
                urgent_button = False
        
        with col3:
            clear_button = st.form_submit_button("🗑️ Clear Chat", use_container_width=True)
    
    # Handle form submissions
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.current_query = ""
        st.rerun()
    
    # Process query
    if (ask_button or urgent_button) and query.strip():
        # Add urgency context for HR personnel
        if urgent_button and st.session_state.user_role == "HR Personnel":
            query = f"[URGENT] {query}"
        
        with st.spinner("🤔 Processing your question... Please wait"):
            try:
                router = init_query_router()
                response = router.ask(query)
                
                # Display response with enhanced information
                display_response(response, show_metadata=(st.session_state.user_role == "HR Personnel" and show_metadata))
                
                # Add role context to response
                response['user_role'] = st.session_state.user_role
                response['is_urgent'] = urgent_button
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'query': query,
                    'response': response,
                    'timestamp': datetime.now(),
                    'role': st.session_state.user_role
                })
                
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                st.info("💡 Please try rephrasing your question or contact support if the issue persists.")
        
        st.session_state.current_query = ""
        st.rerun()
    
    # Sample questions section
    if not st.session_state.chat_history:
        st.markdown("---")
        st.markdown(f"### 🎯 Popular {st.session_state.user_role} Questions")
        st.markdown("*Click on any question to try it:*")
        
        sample_questions = get_role_specific_questions()
        
        # Create 2 columns for questions
        col1, col2 = st.columns(2)
        
        for i, question in enumerate(sample_questions):
            col_idx = i % 2
            with [col1, col2][col_idx]:
                if st.button(question, key=f"sample_{i}", use_container_width=True):
                    st.session_state.current_query = question
                    st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 📝 Conversation History")
        
        # Show recent conversations
        for i, chat in enumerate(reversed(st.session_state.chat_history[-3:])):  # Show last 3
            chat_number = len(st.session_state.chat_history) - i
            
            # Chat header with role and urgency indicators
            role_emoji = "👤" if chat['role'] == "Employee" else "🏢"
            urgent_indicator = "🚨 " if chat['response'].get('is_urgent', False) else ""
            
            st.markdown(f"#### {role_emoji} {urgent_indicator}Question {chat_number}")
            st.markdown(f"**{chat['query']}**")
            st.caption(f"Asked at: {chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} ({chat['role']} View)")
            
            # Display response
            display_response(chat['response'], show_metadata and st.session_state.user_role == "HR Personnel")
            
            st.markdown("---")
        
        # Show more conversations if available
        if len(st.session_state.chat_history) > 3:
            with st.expander(f"📚 View All {len(st.session_state.chat_history)} Conversations"):
                for i, chat in enumerate(reversed(st.session_state.chat_history)):
                    chat_number = len(st.session_state.chat_history) - i
                    role_emoji = "👤" if chat['role'] == "Employee" else "🏢"
                    
                    with st.container():
                        st.markdown(f"**{role_emoji} Q{chat_number}:** {chat['query']}")
                        st.markdown(f"**Answer:** {chat['response']['answer'][:150]}...")
                        st.markdown(f"**Confidence:** {chat['response']['confidence_level']} | **Time:** {chat['timestamp'].strftime('%H:%M:%S')}")
                        if chat['response'].get('query_type'):
                            st.markdown(f"**Type:** {chat['response']['query_type'].replace('_', ' ').title()}")
                        st.markdown("---")

def render_document_generator():
    """Render document generation interface"""
    st.markdown("## 📄 Document Generator")
    st.markdown("*Generate HR documents using organization templates*")
    
    try:
        from document_generator import DocumentGenerator
        doc_gen = DocumentGenerator()
        
        # Install sample templates if none exist
        templates = doc_gen.get_available_templates()
        if not any(templates.values()):
            if st.button("📥 Install Sample Templates"):
                count = doc_gen.install_sample_templates()
                st.success(f"✅ Installed {count} sample templates!")
                st.rerun()
            st.info("💡 No templates found. Install sample templates to get started.")
            return
        
        # Template selection
        st.markdown("### 📋 Select Template")
        
        # Category tabs
        categories = [cat for cat, templates_list in templates.items() if templates_list]
        if categories:
            selected_category = st.selectbox("Select category:", categories)
            
            # Template selection within category
            category_templates = templates[selected_category]
            template_options = {t['name']: t for t in category_templates}
            selected_template_name = st.selectbox("Select template:", list(template_options.keys()))
            selected_template = template_options[selected_template_name]
            
            st.markdown("### 📝 Template Data")
            
            # Initialize session state for template data
            if 'template_data' not in st.session_state:
                st.session_state.template_data = {}
            
            # Dynamic form based on template type
            if selected_template_name == 'offer_letter':
                template_data = render_offer_letter_form()
            elif selected_template_name == 'termination_letter':
                template_data = render_termination_letter_form()
            elif selected_template_name == 'experience_certificate':
                template_data = render_experience_certificate_form()
            else:
                template_data = render_generic_form()
            
            # Store template data in session state when form is submitted
            if template_data:
                st.session_state.template_data = template_data
                st.success("✅ Template data prepared!")
            
            # Output format selection
            col1, col2 = st.columns(2)
            with col1:
                output_format = st.selectbox("Output format:", ['html', 'docx', 'pdf'])
            with col2:
                st.write("")  # Spacing
            
            # Generate button - only enabled if we have template data
            generate_enabled = bool(st.session_state.template_data)
            
            if st.button("🚀 Generate Document", type="primary", use_container_width=True, disabled=not generate_enabled):
                if st.session_state.template_data:
                    with st.spinner("Generating document..."):
                        try:
                            result = doc_gen.generate_document(
                                selected_template_name, 
                                st.session_state.template_data, 
                                output_format
                            )
                            
                            if result.get('success', False):
                                st.success(f"✅ Document generated: {result['filename']}")
                                
                                # Show download button based on format
                                if result['type'] == 'html' and 'content' in result:
                                    st.download_button(
                                        label="📥 Download HTML Document",
                                        data=result['content'],
                                        file_name=result['filename'],
                                        mime="text/html"
                                    )
                                elif result['type'] == 'docx' and 'content' in result:
                                    st.download_button(
                                        label="📥 Download Word Document",
                                        data=result['content'],
                                        file_name=result['filename'],
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                                elif result['type'] == 'pdf' and 'content' in result:
                                    st.download_button(
                                        label="📥 Download PDF Document",
                                        data=result['content'],
                                        file_name=result['filename'],
                                        mime="application/pdf"
                                    )
                                
                                # Show preview for HTML only, info for others
                                if result['type'] == 'html' and 'content' in result:
                                    with st.expander("👁️ Document Preview"):
                                        st.components.v1.html(result['content'], height=600, scrolling=True)
                                elif result['type'] == 'docx':
                                    st.info("💡 Word document generated successfully. Use the download button above to save it.")
                                elif result['type'] == 'pdf':
                                    st.info("💡 PDF document generated successfully. Use the download button above to save it.")
                            else:
                                st.error(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                                
                                # Show installation instructions for PDF if that's the issue
                                error_msg = result.get('error', '')
                                if 'PDF generation requires additional libraries' in error_msg:
                                    st.markdown("### 📦 Installation Instructions")
                                    st.code("""
# Install PDF generation libraries (choose one):

# Option 1: WeasyPrint (Recommended - better HTML rendering)
pip install weasyprint

# Option 2: ReportLab (Lighter weight)
pip install reportlab

# If you encounter issues with WeasyPrint on Windows:
# You may need to install GTK+ or use WSL
                                    """, language="bash")
                                    
                                    st.info("💡 After installation, restart your Streamlit app to enable PDF generation.")
                                
                                # Debug information
                                with st.expander("🔍 Debug Information"):
                                    st.json({
                                        'template_data': result.get('template_data', {}),
                                        'template_info': result.get('template_info', {}),
                                        'error': result.get('error', 'No error info')
                                    })
                        
                        except Exception as e:
                            st.error(f"❌ Generation failed: {str(e)}")
                            with st.expander("🔍 Debug Information"):
                                st.json({
                                    'template_data': st.session_state.template_data,
                                    'selected_template': selected_template_name,
                                    'error': str(e)
                                })
                else:
                    st.warning("⚠️ Please fill in the template data first!")
            
            # Show current template data for debugging
            if st.session_state.template_data:
                with st.expander("🔍 Current Template Data"):
                    st.json(st.session_state.template_data)
        
    except ImportError:
        st.error("❌ Document generator not available. Please ensure document_generator.py is in your project.")
    except Exception as e:
        st.error(f"❌ Document generator error: {str(e)}")

def render_offer_letter_form():
    """Render form for offer letter template"""
    st.markdown("#### 📋 Offer Letter Information")
    
    with st.form("offer_letter_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input("Employee Name*", placeholder="John Doe", key="ol_emp_name")
            position_title = st.text_input("Position Title*", placeholder="Software Engineer", key="ol_position")
            department = st.text_input("Department*", placeholder="Engineering", key="ol_dept")
            employment_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract"], key="ol_emp_type")
        
        with col2:
            start_date = st.date_input("Start Date*", key="ol_start_date")
            salary = st.number_input("Annual Salary*", min_value=0, value=50000, key="ol_salary")
            response_deadline = st.date_input("Response Deadline*", key="ol_deadline")
            hr_manager_name = st.text_input("HR Manager Name*", placeholder="Jane Smith", key="ol_hr_manager")
        
        company_name = st.text_input("Company Name", value="Adanian Labs", key="ol_company")
        
        submitted = st.form_submit_button("✅ Prepare Template Data", use_container_width=True)
        
        if submitted:
            # Validation
            required_fields = {
                'Employee Name': employee_name,
                'Position Title': position_title,
                'Department': department,
                'HR Manager Name': hr_manager_name
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value.strip()]
            
            if missing_fields:
                st.error(f"❌ Please fill in required fields: {', '.join(missing_fields)}")
                return {}
            
            return {
                'employee_name': employee_name.strip(),
                'position_title': position_title.strip(),
                'department': department.strip(),
                'start_date': start_date.isoformat(),
                'salary': salary,
                'employment_type': employment_type,
                'response_deadline': response_deadline.isoformat(),
                'hr_manager_name': hr_manager_name.strip(),
                'company_name': company_name.strip()
            }
    
    return {}

def render_termination_letter_form():
    """Render form for termination letter template"""
    st.markdown("#### 📋 Termination Letter Information")
    
    with st.form("termination_letter_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input("Employee Name*", key="tl_emp_name")
            employee_id = st.text_input("Employee ID*", key="tl_emp_id")
            position_title = st.text_input("Position Title*", key="tl_position")
            department = st.text_input("Department*", key="tl_dept")
        
        with col2:
            termination_date = st.date_input("Termination Date*", key="tl_term_date")
            last_working_day = st.date_input("Last Working Day*", key="tl_last_day")
            termination_reason = st.text_input("Termination Reason*", key="tl_reason")
            hr_manager_name = st.text_input("HR Manager Name*", key="tl_hr_manager")
        
        # Settlement details
        st.markdown("#### Final Settlement (Optional)")
        col3, col4 = st.columns(2)
        
        with col3:
            final_salary = st.number_input("Final Salary", min_value=0, value=0, key="tl_final_salary")
            unused_leave_days = st.number_input("Unused Leave Days", min_value=0, value=0, key="tl_leave_days")
        
        with col4:
            unused_leave_amount = st.number_input("Leave Amount", min_value=0, value=0, key="tl_leave_amount")
            total_settlement = st.number_input("Total Settlement", min_value=0, value=0, key="tl_total")
        
        company_name = st.text_input("Company Name", value="Adanian Labs", key="tl_company")
        
        submitted = st.form_submit_button("✅ Prepare Template Data", use_container_width=True)
        
        if submitted:
            # Validation
            required_fields = {
                'Employee Name': employee_name,
                'Employee ID': employee_id,
                'Position Title': position_title,
                'Department': department,
                'Termination Reason': termination_reason,
                'HR Manager Name': hr_manager_name
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value.strip()]
            
            if missing_fields:
                st.error(f"❌ Please fill in required fields: {', '.join(missing_fields)}")
                return {}
            
            data = {
                'employee_name': employee_name.strip(),
                'employee_id': employee_id.strip(),
                'position_title': position_title.strip(),
                'department': department.strip(),
                'termination_date': termination_date.isoformat(),
                'last_working_day': last_working_day.isoformat(),
                'termination_reason': termination_reason.strip(),
                'hr_manager_name': hr_manager_name.strip(),
                'company_name': company_name.strip()
            }
            
            # Add settlement data if provided
            if any([final_salary, unused_leave_days, unused_leave_amount, total_settlement]):
                data.update({
                    'final_settlement': True,
                    'final_salary': final_salary,
                    'unused_leave_days': unused_leave_days,
                    'unused_leave_amount': unused_leave_amount,
                    'total_settlement': total_settlement
                })
            
            return data
    
    return {}

def render_experience_certificate_form():
    """Render form for experience certificate template"""
    st.markdown("#### 📋 Experience Certificate Information")
    
    with st.form("experience_certificate_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input("Employee Name*", key="ec_emp_name")
            position_title = st.text_input("Position Title*", key="ec_position")
            department = st.text_input("Department*", key="ec_dept")
            hr_manager_name = st.text_input("HR Manager Name*", key="ec_hr_manager")
        
        with col2:
            start_date = st.date_input("Employment Start Date*", key="ec_start_date")
            end_date = st.date_input("Employment End Date*", key="ec_end_date")
            he_she = st.selectbox("Pronoun", ["They", "He", "She"], key="ec_pronoun")
            was_were = st.selectbox("Verb", ["were", "was"], key="ec_verb")
        
        company_name = st.text_input("Company Name", value="Adanian Labs", key="ec_company")
        
        submitted = st.form_submit_button("✅ Prepare Template Data", use_container_width=True)
        
        if submitted:
            # Validation
            required_fields = {
                'Employee Name': employee_name,
                'Position Title': position_title,
                'Department': department,
                'HR Manager Name': hr_manager_name
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value.strip()]
            
            if missing_fields:
                st.error(f"❌ Please fill in required fields: {', '.join(missing_fields)}")
                return {}
            
            return {
                'employee_name': employee_name.strip(),
                'position_title': position_title.strip(),
                'department': department.strip(),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'hr_manager_name': hr_manager_name.strip(),
                'company_name': company_name.strip(),
                'he_she': he_she,
                'was_were': was_were
            }
    
    return {}

def render_generic_form():
    """Render generic form for custom templates"""
    st.markdown("#### 📋 Generic Document Information")
    
    with st.form("generic_form", clear_on_submit=False):
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input("Employee Name", key="gf_emp_name")
            position_title = st.text_input("Position Title", key="gf_position")
            department = st.text_input("Department", key="gf_dept")
        
        with col2:
            employee_id = st.text_input("Employee ID", key="gf_emp_id")
            hr_manager_name = st.text_input("HR Manager Name", key="gf_hr_manager")
            company_name = st.text_input("Company Name", value="Adanian Labs", key="gf_company")
        
        # Custom fields
        st.markdown("#### Custom Fields")
        custom_data = st.text_area("Custom Data (JSON format)", 
                                  placeholder='{"field1": "value1", "field2": "value2"}', 
                                  key="gf_custom")
        
        submitted = st.form_submit_button("✅ Prepare Template Data", use_container_width=True)
        
        if submitted:
            data = {
                'employee_name': employee_name.strip() if employee_name else '',
                'position_title': position_title.strip() if position_title else '',
                'department': department.strip() if department else '',
                'employee_id': employee_id.strip() if employee_id else '',
                'hr_manager_name': hr_manager_name.strip() if hr_manager_name else '',
                'company_name': company_name.strip() if company_name else 'Adanian Labs'
            }
            
            # Parse custom data
            if custom_data.strip():
                try:
                    import json
                    custom_fields = json.loads(custom_data)
                    data.update(custom_fields)
                except Exception as e:
                    st.warning(f"⚠️ Invalid JSON in custom fields: {str(e)}")
            
            return data
    
    return {}

def render_leave_request_form():
    """Render leave request form for employees"""
    st.markdown("## 📅 Request Leave")
    st.markdown("*Submit a new leave request for HR approval*")
    
    try:
        from leave_management import LeaveManagementService
        leave_service = LeaveManagementService()
        
        with st.form("leave_request_form"):
            st.markdown("### 📝 Leave Request Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                employee_name = st.text_input("Full Name*", placeholder="John Doe")
                employee_email = st.text_input("Email Address*", placeholder="john.doe@adanianlabs.io")
                leave_type = st.selectbox("Leave Type*", [
                    "Annual Leave", "Sick Leave", "Personal Leave", 
                    "Emergency Leave", "Maternity/Paternity Leave", "Study Leave"
                ])
            
            with col2:
                start_date = st.date_input("Start Date*", min_value=date.today())
                end_date = st.date_input("End Date*", min_value=start_date if 'start_date' in locals() else date.today())
                
                # Calculate days
                if start_date and end_date:
                    days_requested = (end_date - start_date).days + 1
                    st.info(f"📊 Days requested: **{days_requested}**")
            
            reason = st.text_area("Reason for Leave*", placeholder="Please provide details about your leave request...")
            
            # Submit button
            submitted = st.form_submit_button("📤 Submit Leave Request", type="primary", use_container_width=True)
            
            if submitted:
                # Validation
                if not all([employee_name, employee_email, leave_type, start_date, end_date, reason]):
                    st.error("❌ Please fill in all required fields marked with *")
                elif start_date > end_date:
                    st.error("❌ End date must be after start date")
                else:
                    # Submit leave request
                    with st.spinner("Submitting leave request..."):
                        result = leave_service.create_leave_request(
                            employee_name=employee_name.strip(),
                            employee_email=employee_email.strip(),
                            leave_type=leave_type,
                            start_date=start_date,
                            end_date=end_date,
                            reason=reason.strip()
                        )
                    
                    if result.get('success'):
                        st.success(f"✅ {result['message']}")
                        st.balloons()
                        time.sleep(2)
                        st.session_state.show_leave_request = False
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result.get('error')}")
        
    except ImportError:
        st.error("❌ Leave management service not available. Please ensure leave_management.py is in your project.")
    except Exception as e:
        st.error(f"❌ Error loading leave request form: {str(e)}")

def render_my_leave_requests():
    """Render employee's leave requests"""
    st.markdown("## 📋 My Leave Requests")
    st.markdown("*View your submitted leave requests and their status*")
    
    try:
        from leave_management import LeaveManagementService
        leave_service = LeaveManagementService()
        
        # Employee email input
        employee_email = st.text_input("Your Email Address", placeholder="john.doe@adanianlabs.io")
        
        if employee_email:
            with st.spinner("Loading your leave requests..."):
                leave_requests = leave_service.get_employee_leave_requests(employee_email.strip())
            
            if not leave_requests:
                st.info("📭 No leave requests found for this email address")
                return
            
            st.markdown(f"### 📊 Found {len(leave_requests)} leave requests")
            
            # Display leave requests
            for i, request in enumerate(leave_requests):
                status = request.get('status', 'unknown')
                
                # Status styling
                if status == 'approved':
                    status_color = "🟢"
                    status_style = "success"
                elif status == 'rejected':
                    status_color = "🔴"
                    status_style = "error"
                else:
                    status_color = "🟡"
                    status_style = "warning"
                
                with st.expander(f"{status_color} Request #{request.get('id')} - {request.get('leave_type')} ({status.upper()})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📅 Dates:** {request.get('start_date')} to {request.get('end_date')}")
                        st.write(f"**📊 Days:** {request.get('days_requested')}")
                        st.write(f"**📝 Reason:** {request.get('reason')}")
                    
                    with col2:
                        st.write(f"**📤 Submitted:** {request.get('request_date', '')[:10]}")
                        
                        if status_style == "success":
                            st.success(f"✅ **APPROVED**")
                        elif status_style == "error":
                            st.error(f"❌ **REJECTED**")
                        else:
                            st.warning(f"⏳ **PENDING**")
                        
                        if request.get('hr_reviewer'):
                            st.write(f"**👤 Reviewer:** {request.get('hr_reviewer')}")
        
    except ImportError:
        st.error("❌ Leave management service not available.")
    except Exception as e:
        st.error(f"❌ Error loading leave requests: {str(e)}")

def render_hr_leave_management():
    """Render leave management for HR personnel"""
    st.markdown("## 📅 Leave Management")
    st.markdown("*Review and manage employee leave requests*")
    
    try:
        from leave_management import LeaveManagementService
        leave_service = LeaveManagementService()
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["🔍 Pending Requests", "📊 All Requests", "📈 Statistics"])
        
        with tab1:
            st.markdown("### ⏳ Pending Leave Requests")
            
            with st.spinner("Loading pending requests..."):
                pending_requests = leave_service.get_all_leave_requests(status='pending')
            
            if not pending_requests:
                st.success("✅ No pending leave requests")
                return
            
            for request in pending_requests:
                with st.expander(f"🟡 {request.get('employee_name')} - {request.get('leave_type')} ({request.get('days_requested')} days)"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**👤 Employee:** {request.get('employee_name')} ({request.get('employee_email')})")
                        st.write(f"**📅 Dates:** {request.get('start_date')} to {request.get('end_date')}")
                        st.write(f"**📝 Reason:** {request.get('reason')}")
                        st.write(f"**📤 Submitted:** {request.get('request_date', '')[:10]}")
                        if request.get('emergency_contact'):
                            st.write(f"**📞 Emergency:** {request.get('emergency_contact')}")
                    
                    with col2:
                        st.markdown("#### 🔧 Actions")
                        
                        hr_reviewer = st.text_input("Your Name", key=f"reviewer_{request['id']}", placeholder="HR Manager")
                        hr_comments = st.text_area("Comments", key=f"comments_{request['id']}", placeholder="Reason for approval/rejection...")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Approve", key=f"approve_{request['id']}", type="primary"):
                                if hr_reviewer and hr_comments:
                                    result = leave_service.update_leave_request_status(
                                        request['id'], 'approved', hr_comments, hr_reviewer
                                    )
                                    if result.get('success'):
                                        st.success("✅ Request approved!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {result.get('error')}")
                                else:
                                    st.warning("⚠️ Please fill in your name and comments")
                        
                        with col_b:
                            if st.button("❌ Reject", key=f"reject_{request['id']}", type="secondary"):
                                if hr_reviewer and hr_comments:
                                    result = leave_service.update_leave_request_status(
                                        request['id'], 'rejected', hr_comments, hr_reviewer
                                    )
                                    if result.get('success'):
                                        st.success("✅ Request rejected!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {result.get('error')}")
                                else:
                                    st.warning("⚠️ Please fill in your name and comments")
        
        with tab2:
            st.markdown("### 📋 All Leave Requests")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All", "pending", "approved", "rejected"])
            
            with col2:
                limit = st.selectbox("Show", [10, 25, 50, 100], index=1)
            
            # Load requests
            with st.spinner("Loading all requests..."):
                all_requests = leave_service.get_all_leave_requests(
                    status=None if status_filter == "All" else status_filter
                )[:limit]
            
            if not all_requests:
                st.info("📭 No leave requests found")
                return
            
            # Display as table
            import pandas as pd
            df_data = []
            for request in all_requests:
                status = request.get('status', 'unknown')
                df_data.append({
                    'ID': request.get('id'),
                    'Employee': request.get('employee_name'),
                    'Email': request.get('employee_email'),
                    'Type': request.get('leave_type'),
                    'Start': request.get('start_date'),
                    'End': request.get('end_date'),
                    'Days': request.get('days_requested'),
                    'Status': status.upper(),
                    'Submitted': request.get('request_date', '')[:10],
                    'Reviewer': request.get('hr_reviewer', ''),
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        with tab3:
            st.markdown("### 📈 Leave Statistics")
            
            with st.spinner("Calculating statistics..."):
                stats = leave_service.get_leave_statistics()
            
            if 'error' in stats:
                st.error(f"❌ Error loading statistics: {stats['error']}")
                return
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Requests", stats.get('total_requests', 0))
            with col2:
                st.metric("⏳ Pending", stats.get('pending_requests', 0))
            with col3:
                st.metric("✅ Approved", stats.get('approved_requests', 0))
            with col4:
                st.metric("❌ Rejected", stats.get('rejected_requests', 0))
            
            # This month's requests
            st.metric("📅 This Month", stats.get('this_month_requests', 0))
            
            # Leave types breakdown
            leave_types = stats.get('leave_types_breakdown', {})
            if leave_types:
                st.markdown("#### 📊 Leave Types Breakdown")
                
                import plotly.express as px
                fig = px.bar(
                    x=list(leave_types.keys()),
                    y=list(leave_types.values()),
                    title="Requests by Leave Type",
                    labels={'x': 'Leave Type', 'y': 'Number of Requests'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.error("❌ Leave management service not available.")
    except Exception as e:
        st.error(f"❌ Error loading leave management: {str(e)}")

def main():
    """Main application function"""
    # Initialize session state first
    initialize_session_state()
    
    # Initialize additional leave-related session state
    if 'show_leave_request' not in st.session_state:
        st.session_state.show_leave_request = False
    if 'show_my_leaves' not in st.session_state:
        st.session_state.show_my_leaves = False
    if 'show_leave_management' not in st.session_state:
        st.session_state.show_leave_management = False
    
    # Initialize services once in session state
    if 'services_initialized' not in st.session_state:
        with st.spinner("Initializing HR Assistant..."):
            st.session_state.hr_dashboard = HRDashboard()
            st.session_state.services_initialized = True
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 HR Assistant - AI Powered</h1>', unsafe_allow_html=True)
    
    # Role information display
    role_emoji = "👤" if st.session_state.user_role == "Employee" else "🏢"
    st.markdown(f'<div class="role-info">Current Role: {role_emoji} <strong>{st.session_state.user_role}</strong></div>', unsafe_allow_html=True)
    
    # Check for employee-specific leave views
    if st.session_state.user_role == "Employee":
        # Handle employee leave requests
        if st.session_state.get('show_leave_request', False):
            if st.button("← Back to Chat"):
                st.session_state.show_leave_request = False
                st.rerun()
            render_leave_request_form()
            return
        
        if st.session_state.get('show_my_leaves', False):
            if st.button("← Back to Chat"):
                st.session_state.show_my_leaves = False
                st.rerun()
            render_my_leave_requests()
            return
        
        # Default employee chat interface
        render_chat_interface()
        return
    
    # HR Personnel get full navigation including leave management
    with st.sidebar:
        st.title("🏢 Adanian Labs")
        st.markdown("**HR Assistant & Analytics**")
        st.markdown("---")
        
        page = st.radio(
            "Navigate to:",
            [
                "💬 HR Assistant", 
                "📊 Live Dashboard",
                "📄 Document Generator",
                "📅 Leave Management"  # MOVED HERE
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 🔗 Quick Actions")
        
        if st.button("🔄 Refresh All Data", use_container_width=True):
            # Clear all session state data except core settings
            for key in list(st.session_state.keys()):
                if key.startswith(('dashboard_', 'employee_', 'chat_')):
                    del st.session_state[key]
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            st.success("✅ Data refreshed!")
            st.rerun()
    
    # Main content area for HR Personnel
    if page == "💬 HR Assistant":
        render_chat_interface()
    elif page == "📊 Live Dashboard":
        st.session_state.hr_dashboard.render_dashboard()
    elif page == "📄 Document Generator":
        render_document_generator()
    elif page == "📅 Leave Management":  # ADDED THIS
        render_hr_leave_management()

if __name__ == "__main__":
    main()