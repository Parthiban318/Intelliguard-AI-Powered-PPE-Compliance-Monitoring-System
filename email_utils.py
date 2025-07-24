import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import logging
from datetime import datetime
from config import config

class EmailNotificationSystem:
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.username = config.SMTP_USERNAME
        self.password = config.SMTP_PASSWORD
    
    def send_violation_alert(self, violation_data, recipient_emails):
        """Send violation alert email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(recipient_emails)
            msg['Subject'] = f"🚨 PPE Violation Alert - {violation_data.get('violation_type', 'Unknown')}"
            
            # Create email body
            body = self._create_violation_email_body(violation_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            self._send_email(msg, recipient_emails)
            logging.info(f"Violation alert sent to {recipient_emails}")
            
        except Exception as e:
            logging.error(f"Error sending violation alert: {e}")
    
    def send_daily_report(self, report_data, recipient_emails):
        """Send daily compliance report"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(recipient_emails)
            msg['Subject'] = f"📋 Daily PPE Compliance Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            body = self._create_daily_report_body(report_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach CSV if provided
            if 'csv_data' in report_data and report_data['csv_data'] is not None:
                self._attach_csv(msg, report_data['csv_data'], 'daily_violations_report.csv')
            
            # Send email
            self._send_email(msg, recipient_emails)
            logging.info(f"Daily report sent to {recipient_emails}")
            
        except Exception as e:
            logging.error(f"Error sending daily report: {e}")
    
    def send_employee_registration_notification(self, employee_data, admin_emails):
        """Send notification when new employee is registered"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(admin_emails)
            msg['Subject'] = f"👤 New Employee Registration - {employee_data.get('first_name')} {employee_data.get('last_name')}"
            
            body = self._create_employee_registration_body(employee_data)
            msg.attach(MIMEText(body, 'html'))
            
            self._send_email(msg, admin_emails)
            logging.info(f"Employee registration notification sent to {admin_emails}")
            
        except Exception as e:
            logging.error(f"Error sending employee registration notification: {e}")
    
    def _create_violation_email_body(self, violation_data):
        """Create HTML email body for violation alert"""
        severity_color = {
            'CRITICAL': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#28a745'
        }.get(violation_data.get('severity', 'MEDIUM'), '#ffc107')
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; border-bottom: 2px solid #FF6B35; padding-bottom: 20px; margin-bottom: 30px;">
                        <h1 style="color: #FF6B35; margin: 0; font-size: 28px;">🚨 PPE Violation Alert</h1>
                        <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">Intelliguard Safety Monitoring System</p>
                    </div>
                    
                    <div style="background-color: #fff3f3; border-left: 4px solid {severity_color}; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
                        <h2 style="color: {severity_color}; margin: 0 0 15px 0; font-size: 20px;">
                            {violation_data.get('violation_type', 'Unknown').replace('_', ' ').title()} Detected
                        </h2>
                        <p style="margin: 0; font-size: 16px; color: #333;">
                            <strong>Severity:</strong> <span style="color: {severity_color}; font-weight: bold;">{violation_data.get('severity', 'MEDIUM')}</span>
                        </p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">📍 Violation Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Employee:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{violation_data.get('employee_name', 'Unknown')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Department:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{violation_data.get('department', 'Unknown')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Detection Time:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{violation_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Confidence:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{violation_data.get('confidence', 0):.2f}%</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #fff8e1; border: 1px solid #ffc107; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                        <h3 style="color: #e65100; margin: 0 0 10px 0; font-size: 16px;">⚠️ Immediate Action Required</h3>
                        <p style="margin: 0; color: #333; line-height: 1.5;">
                            Please ensure the employee is properly equipped with required PPE before continuing work activities.
                            Safety protocols must be followed at all times to prevent accidents and maintain compliance.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="margin: 0; color: #888; font-size: 14px;">
                            This is an automated alert from Intelliguard PPE Monitoring System<br>
                            Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        return body
    
    def _create_daily_report_body(self, report_data):
        """Create HTML email body for daily report"""
        compliance_rate = report_data.get('compliance_rate', 0)
        compliance_color = '#28a745' if compliance_rate >= 90 else '#ffc107' if compliance_rate >= 70 else '#dc3545'
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; border-bottom: 2px solid #2E86AB; padding-bottom: 20px; margin-bottom: 30px;">
                        <h1 style="color: #2E86AB; margin: 0; font-size: 28px;">📋 Daily PPE Compliance Report</h1>
                        <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">
                            {datetime.now().strftime('%A, %B %d, %Y')}
                        </p>
                    </div>
                    
                    <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                        <div style="flex: 1; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid {compliance_color};">
                            <h3 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">Overall Compliance</h3>
                            <p style="margin: 0; font-size: 32px; font-weight: bold; color: {compliance_color};">
                                {compliance_rate:.1f}%
                            </p>
                        </div>
                        <div style="flex: 1; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8;">
                            <h3 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">Total Detections</h3>
                            <p style="margin: 0; font-size: 32px; font-weight: bold; color: #17a2b8;">
                                {report_data.get('total_detections', 0)}
                            </p>
                        </div>
                        <div style="flex: 1; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #dc3545;">
                            <h3 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">Violations</h3>
                            <p style="margin: 0; font-size: 32px; font-weight: bold; color: #dc3545;">
                                {report_data.get('total_violations', 0)}
                            </p>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #333; margin: 0 0 15px 0; font-size: 20px;">🏢 Department Summary</h3>
                        <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                            <thead>
                                <tr style="background-color: #2E86AB; color: white;">
                                    <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Department</th>
                                    <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Detections</th>
                                    <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Violations</th>
                                    <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Compliance Rate</th>
                                </tr>
                            </thead>
                            <tbody>
        """
        
        # Add department data if available
        for dept_data in report_data.get('department_summary', []):
            dept_compliance = dept_data.get('compliance_rate', 0)
            dept_color = '#28a745' if dept_compliance >= 90 else '#ffc107' if dept_compliance >= 70 else '#dc3545'
            body += f"""
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 10px; border: 1px solid #ddd;">{dept_data.get('department', 'Unknown')}</td>
                                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{dept_data.get('detections', 0)}</td>
                                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{dept_data.get('violations', 0)}</td>
                                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd; color: {dept_color}; font-weight: bold;">
                                        {dept_compliance:.1f}%
                                    </td>
                                </tr>
            """
        
        body += f"""
                            </tbody>
                        </table>
                    </div>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #333; margin: 0 0 15px 0; font-size: 20px;">⚠️ Top Violation Types</h3>
                        <div style="background-color: #fff3f3; border: 1px solid #dc3545; border-radius: 5px; padding: 15px;">
        """
        
        # Add violation type data if available
        for violation in report_data.get('top_violations', [])[:5]:
            body += f"""
                            <p style="margin: 5px 0; color: #333;">
                                <strong>{violation.get('type', 'Unknown').replace('_', ' ').title()}:</strong> 
                                {violation.get('count', 0)} occurrences
                            </p>
            """
        
        body += f"""
                        </div>
                    </div>
                    
                    <div style="background-color: #e8f4f8; border: 1px solid #17a2b8; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                        <h3 style="color: #0c5460; margin: 0 0 10px 0; font-size: 16px;">💡 Recommendations</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #333; line-height: 1.6;">
                            <li>Schedule additional safety training for departments with compliance rates below 90%</li>
                            <li>Ensure adequate PPE equipment is available at all workstations</li>
                            <li>Review and reinforce safety protocols with employees</li>
                            <li>Consider implementing additional safety measures for high-risk areas</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="margin: 0; color: #888; font-size: 14px;">
                            This automated report was generated by Intelliguard PPE Monitoring System<br>
                            Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        return body
    
    def _create_employee_registration_body(self, employee_data):
        """Create HTML email body for employee registration notification"""
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; border-bottom: 2px solid #28a745; padding-bottom: 20px; margin-bottom: 30px;">
                        <h1 style="color: #28a745; margin: 0; font-size: 28px;">👤 New Employee Registration</h1>
                        <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">Intelliguard Safety Monitoring System</p>
                    </div>
                    
                    <div style="background-color: #f8fff8; border-left: 4px solid #28a745; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
                        <h2 style="color: #28a745; margin: 0 0 15px 0; font-size: 20px;">
                            New Employee Added to System
                        </h2>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">📋 Employee Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Name:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Username:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{employee_data.get('username', '')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Email:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{employee_data.get('email', '')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Department:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{employee_data.get('department', '')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; color: #555;">Role:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #333;">{employee_data.get('role', 'user').title()}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Registration Date:</td>
                                <td style="padding: 8px 0; color: #333;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="margin: 0; color: #888; font-size: 14px;">
                            This notification was automatically generated by Intelliguard PPE Monitoring System<br>
                            Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        return body
    
    def _attach_csv(self, msg, csv_data, filename):
        """Attach CSV file to email"""
        if isinstance(csv_data, pd.DataFrame):
            csv_string = csv_data.to_csv(index=False)
        else:
            csv_string = csv_data
        
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(csv_string.encode())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        msg.attach(attachment)
    
    def _send_email(self, msg, recipient_emails):
        """Send email using SMTP"""
        if not all([self.smtp_server, self.smtp_port, self.username, self.password]):
            logging.error("SMTP configuration incomplete")
            return
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            for email in recipient_emails:
                server.sendmail(self.username, email, msg.as_string())
            
            server.quit()
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")

# Initialize email system
email_system = EmailNotificationSystem()