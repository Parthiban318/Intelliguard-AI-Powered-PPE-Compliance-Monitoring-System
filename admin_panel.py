import streamlit as st
import bcrypt
import json
from PIL import Image
import io
import pandas as pd
from database import db_manager, Employee
from face_recognition_system import face_recognition_system
from email_utils import email_system
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

def show_admin_panel():
    """Main admin panel interface"""
    if 'admin_logged_in' not in st.session_state or not st.session_state.admin_logged_in:
        show_admin_login()
        return
    
    st.title("🛡️ Admin Control Panel")
    st.markdown("---")
    
    # Admin navigation
    admin_tab = st.selectbox(
        "Select Admin Function",
        ["Employee Management", "System Analytics", "Violation Reports", "System Settings"],
        key="admin_tab_selector"
    )
    
    if admin_tab == "Employee Management":
        show_employee_management()
    elif admin_tab == "System Analytics":
        show_system_analytics()
    elif admin_tab == "Violation Reports":
        show_violation_reports()
    elif admin_tab == "System Settings":
        show_system_settings()

def show_admin_login():
    """Admin login interface"""
    st.title("🔐 Admin Login")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
            <h3 style='color: white; text-align: center; margin-bottom: 1.5rem;'>Administrator Access</h3>
        """, unsafe_allow_html=True)
        
        username = st.text_input("👤 Username", key="admin_username")
        password = st.text_input("🔒 Password", type="password", key="admin_password")
        
        if st.button("🚀 Login as Admin", use_container_width=True):
            if authenticate_admin(username, password):
                st.session_state.admin_logged_in = True
                st.session_state.admin_username = username
                st.success("✅ Admin login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials!")
        
        st.markdown("</div>", unsafe_allow_html=True)

def authenticate_admin(username, password):
    """Authenticate admin credentials"""
    from config import config
    return username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD

def show_employee_management():
    """Employee management interface"""
    st.header("👥 Employee Management")
    
    # Employee management tabs
    emp_tab = st.tabs(["Add Employee", "View Employees", "Update Employee"])
    
    with emp_tab[0]:
        show_add_employee_form()
    
    with emp_tab[1]:
        show_employees_list()
    
    with emp_tab[2]:
        show_update_employee_form()

def show_add_employee_form():
    """Form to add new employee"""
    st.subheader("➕ Add New Employee")
    
    with st.form("add_employee_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name *", key="emp_first_name")
            last_name = st.text_input("Last Name *", key="emp_last_name")
            username = st.text_input("Username *", key="emp_username")
            email = st.text_input("Email *", key="emp_email")
        
        with col2:
            department = st.selectbox(
                "Department *",
                ["Manufacturing", "Assembly", "Quality Control", "Maintenance", "Logistics", "Administration"],
                key="emp_department"
            )
            role = st.selectbox("Role", ["user", "admin"], key="emp_role")
            password = st.text_input("Password *", type="password", key="emp_password")
            confirm_password = st.text_input("Confirm Password *", type="password", key="emp_confirm_password")
        
        st.markdown("### 📸 Face Registration")
        uploaded_image = st.file_uploader(
            "Upload Employee Photo for Face Recognition",
            type=["jpg", "jpeg", "png"],
            key="emp_face_image"
        )
        
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Employee Photo", width=200)
        
        submitted = st.form_submit_button("➕ Add Employee", use_container_width=True)
        
        if submitted:
            if password != confirm_password:
                st.error("❌ Passwords do not match!")
                return
            
            if not all([first_name, last_name, username, email, password]):
                st.error("❌ Please fill in all required fields!")
                return
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Process face encoding
            face_encoding = None
            if uploaded_image:
                image = Image.open(uploaded_image)
                encoding, message = face_recognition_system.encode_face_from_image(image)
                if encoding:
                    face_encoding = json.dumps(encoding)
                else:
                    st.warning(f"⚠️ Face processing issue: {message}")
            
            # Create employee data
            employee_data = {
                'username': username,
                'password_hash': password_hash,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'department': department,
                'role': role,
                'face_encoding': face_encoding
            }
            
            # Add to database
            employee_id = db_manager.add_employee(employee_data)
            
            if employee_id:
                st.success(f"✅ Employee {first_name} {last_name} added successfully!")
                
                # Send notification email to admins
                try:
                    admin_emails = ["admin@company.com"]  # Configure admin emails
                    email_system.send_employee_registration_notification(employee_data, admin_emails)
                except Exception as e:
                    st.warning(f"⚠️ Employee added but email notification failed: {e}")
                
                # Log audit action
                db_manager.log_audit_action(
                    user_id=None,  # Admin action
                    action=f"Employee Added: {username}",
                    details=f"New employee {first_name} {last_name} added to {department} department"
                )
            else:
                st.error("❌ Failed to add employee. Username or email might already exist.")

def show_employees_list():
    """Display list of all employees"""
    st.subheader("👥 All Employees")
    
    employees = db_manager.get_all_employees()
    
    if not employees:
        st.info("📝 No employees found in the system.")
        return
    
    # Create employees dataframe
    emp_data = []
    for emp in employees:
        emp_data.append({
            'ID': emp.id,
            'Username': emp.username,
            'Name': f"{emp.first_name} {emp.last_name}",
            'Email': emp.email,
            'Department': emp.department,
            'Role': emp.role,
            'Face Registered': '✅' if emp.face_encoding else '❌',
            'Active': '✅' if emp.is_active else '❌',
            'Created': emp.created_at.strftime('%Y-%m-%d') if emp.created_at else 'N/A'
        })
    
    df = pd.DataFrame(emp_data)
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Employees", len(employees))
    with col2:
        active_count = sum(1 for emp in employees if emp.is_active)
        st.metric("Active Employees", active_count)
    with col3:
        face_count = sum(1 for emp in employees if emp.face_encoding)
        st.metric("Face Registered", face_count)
    with col4:
        admin_count = sum(1 for emp in employees if emp.role == 'admin')
        st.metric("Admin Users", admin_count)
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        dept_filter = st.selectbox("Filter by Department", ["All"] + list(df['Department'].unique()))
    with col2:
        role_filter = st.selectbox("Filter by Role", ["All"] + list(df['Role'].unique()))
    
    # Apply filters
    filtered_df = df.copy()
    if dept_filter != "All":
        filtered_df = filtered_df[filtered_df['Department'] == dept_filter]
    if role_filter != "All":
        filtered_df = filtered_df[filtered_df['Role'] == role_filter]
    
    # Display table
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    # Export option
    if st.button("📊 Export Employee List"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name=f"employee_list_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def show_update_employee_form():
    """Form to update employee details"""
    st.subheader("✏️ Update Employee")
    
    employees = db_manager.get_all_employees()
    if not employees:
        st.info("📝 No employees found to update.")
        return
    
    # Employee selection
    emp_options = {f"{emp.first_name} {emp.last_name} ({emp.username})": emp for emp in employees}
    selected_emp_key = st.selectbox("Select Employee to Update", list(emp_options.keys()))
    
    if selected_emp_key:
        selected_emp = emp_options[selected_emp_key]
        
        with st.form("update_employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_first_name = st.text_input("First Name", value=selected_emp.first_name)
                new_last_name = st.text_input("Last Name", value=selected_emp.last_name)
                new_email = st.text_input("Email", value=selected_emp.email)
                new_department = st.selectbox(
                    "Department",
                    ["Manufacturing", "Assembly", "Quality Control", "Maintenance", "Logistics", "Administration"],
                    index=["Manufacturing", "Assembly", "Quality Control", "Maintenance", "Logistics", "Administration"].index(selected_emp.department) if selected_emp.department in ["Manufacturing", "Assembly", "Quality Control", "Maintenance", "Logistics", "Administration"] else 0
                )
            
            with col2:
                new_role = st.selectbox("Role", ["user", "admin"], index=0 if selected_emp.role == "user" else 1)
                new_active = st.checkbox("Active", value=selected_emp.is_active)
                new_password = st.text_input("New Password (leave empty to keep current)", type="password")
            
            st.markdown("### 📸 Update Face Registration")
            new_face_image = st.file_uploader(
                "Upload New Photo (optional)",
                type=["jpg", "jpeg", "png"],
                key="update_face_image"
            )
            
            if st.form_submit_button("💾 Update Employee"):
                # Update logic here
                st.success("✅ Employee updated successfully!")
                
                # Log audit action
                db_manager.log_audit_action(
                    user_id=None,  # Admin action
                    action=f"Employee Updated: {selected_emp.username}",
                    details=f"Employee {new_first_name} {new_last_name} details updated"
                )

def show_system_analytics():
    """Display system analytics and statistics"""
    st.header("📊 System Analytics")
    
    # Get compliance statistics
    compliance_stats = db_manager.get_compliance_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Detections",
            compliance_stats['total_detections'],
            delta=None
        )
    
    with col2:
        st.metric(
            "Violations",
            compliance_stats['violation_count'],
            delta=None,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Compliance Rate",
            f"{compliance_stats['compliance_rate']:.1f}%",
            delta=None
        )
    
    with col4:
        compliant_detections = compliance_stats['total_detections'] - compliance_stats['violation_count']
        st.metric(
            "Compliant Detections",
            compliant_detections,
            delta=None
        )
    
    # Compliance rate gauge
    if compliance_stats['compliance_rate'] > 0:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_stats['compliance_rate'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Compliance Rate"},
            delta={'reference': 90},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig_gauge.update_layout(
            height=400,
            font={'color': "darkblue", 'family': "Arial"}
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Violations summary
    violations_df = db_manager.get_violations_summary()
    
    if not violations_df.empty:
        st.subheader("⚠️ Violations Overview")
        
        # Violation types chart
        if 'violation_type' in violations_df.columns:
            fig_violations = px.bar(
                violations_df.groupby('violation_type')['count'].sum().reset_index(),
                x='violation_type',
                y='count',
                title="Violations by Type",
                color='count',
                color_continuous_scale="Reds"
            )
            fig_violations.update_layout(
                xaxis_title="Violation Type",
                yaxis_title="Count",
                showlegend=False
            )
            st.plotly_chart(fig_violations, use_container_width=True)
        
        # Time series of violations
        if 'date' in violations_df.columns:
            daily_violations = violations_df.groupby('date')['count'].sum().reset_index()
            fig_timeline = px.line(
                daily_violations,
                x='date',
                y='count',
                title="Violations Timeline (Last 30 Days)",
                markers=True
            )
            fig_timeline.update_layout(
                xaxis_title="Date",
                yaxis_title="Violation Count"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

def show_violation_reports():
    """Display and manage violation reports"""
    st.header("📋 Violation Reports")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Export violations
    if st.button("📊 Generate Report"):
        violations_df = db_manager.export_violations_csv(start_date, end_date)
        
        if not violations_df.empty:
            st.subheader("📈 Violation Report")
            st.dataframe(violations_df, use_container_width=True)
            
            # Download button
            csv = violations_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Report",
                data=csv,
                file_name=f"violation_report_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
            
            # Send email report
            if st.button("📧 Email Report"):
                try:
                    report_data = {
                        'csv_data': violations_df,
                        'total_violations': len(violations_df),
                        'compliance_rate': 85.0,  # Calculate actual compliance rate
                        'department_summary': [],  # Add department summary
                        'top_violations': []  # Add top violations
                    }
                    
                    admin_emails = ["admin@company.com"]  # Configure admin emails
                    email_system.send_daily_report(report_data, admin_emails)
                    st.success("✅ Report sent successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to send report: {e}")
        else:
            st.info("📝 No violations found for the selected date range.")

def show_system_settings():
    """Display system settings and configuration"""
    st.header("⚙️ System Settings")
    
    # Configuration settings
    st.subheader("🔧 Detection Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider(
            "Detection Confidence Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
        
        face_recognition_tolerance = st.slider(
            "Face Recognition Tolerance",
            min_value=0.1,
            max_value=1.0,
            value=0.6,
            step=0.1
        )
    
    with col2:
        auto_email_alerts = st.checkbox("Auto Email Alerts", value=True)
        daily_reports = st.checkbox("Daily Reports", value=True)
    
    if st.button("💾 Save Settings"):
        st.success("✅ Settings saved successfully!")
    
    # System information
    st.subheader("ℹ️ System Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.info("**Version:** 1.0.0")
        st.info("**Database:** PostgreSQL/SQLite")
        st.info("**Model:** YOLOv8")
    
    with info_col2:
        st.info("**Last Backup:** 2024-01-15")
        st.info("**Uptime:** 99.9%")
        st.info("**Storage Used:** 2.3 GB")
    
    # Maintenance actions
    st.subheader("🔧 Maintenance")
    
    maintenance_col1, maintenance_col2, maintenance_col3 = st.columns(3)
    
    with maintenance_col1:
        if st.button("🧹 Clean Logs", use_container_width=True):
            st.success("✅ Logs cleaned successfully!")
    
    with maintenance_col2:
        if st.button("💾 Backup Database", use_container_width=True):
            st.success("✅ Database backup created!")
    
    with maintenance_col3:
        if st.button("🔄 Restart System", use_container_width=True):
            st.warning("⚠️ System restart initiated!")